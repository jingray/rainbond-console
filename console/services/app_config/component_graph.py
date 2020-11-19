# -*- coding: utf8 -*-
import subprocess
import logging
import platform
import json
import os

from django.db import transaction

from console.models.main import ComponentGraph
from goodrain_web.settings import BASE_DIR
from console.exception.main import AbortRequest
from console.exception.bcode import ErrInternalGraphsNotFound
from console.repositories.component_graph import component_graph_repo
from www.utils.crypt import make_uuid

logger = logging.getLogger("default")


class ComponentGraphService(object):
    @staticmethod
    def _load_internal_graphs():
        filenames = []
        internal_graphs = {}
        path_to_graphs = BASE_DIR + "/hack/component-graphs"
        try:
            for filename in os.listdir(path_to_graphs):
                path = path_to_graphs + "/" + filename
                try:
                    with open(path) as f:
                        name, _ = os.path.splitext(filename)
                        internal_graphs[name] = json.load(f)
                        filenames.append(name)
                except ValueError as e:
                    # ignore wrong json file
                    logger.warning(e)
        except OSError as e:
            # directory not found
            logger.warning(e)
        return filenames, internal_graphs

    def list_internal_graphs(self):
        graphs, _ = self._load_internal_graphs()
        return graphs

    def create_internal_graphs(self, component_id, graph_name):
        _, internal_graphs = self._load_internal_graphs()
        if not internal_graphs or not internal_graphs.get(graph_name):
            raise ErrInternalGraphsNotFound

        graphs = []
        seq = self._next_sequence(component_id)
        for graph in internal_graphs.get(graph_name):
            try:
                promql = self.add_or_update_label(component_id, graph["promql"])
            except AbortRequest as e:
                logger.warning("promql {}: {}".format(graph["promql"], e))
                continue
            # make sure there are no duplicate graph
            graphs.append(
                ComponentGraph(
                    component_id=component_id,
                    graph_id=make_uuid(),
                    title=graph["title"],
                    promql=promql,
                    sequence=seq,
                ))
            seq += 1
        ComponentGraph.objects.bulk_create(graphs)

    def create_component_graph(self, component_id, title, promql):
        promql = self.add_or_update_label(component_id, promql)
        graph_id = make_uuid()
        sequence = self._next_sequence(component_id)
        component_graph_repo.create(component_id, graph_id, title, promql, sequence)
        return component_graph_repo.get(component_id, graph_id).to_dict()

    @staticmethod
    def list_component_graphs(component_id):
        graphs = component_graph_repo.list(component_id)
        return [graph.to_dict() for graph in graphs]

    @transaction.atomic()
    def delete_component_graph(self, graph):
        component_graph_repo.delete(graph.component_id, graph.graph_id)
        self._sequence_move_forward(graph.component_id, graph.sequence)

    def delete_by_component_id(self, component_id):
        return component_graph_repo.delete_by_component_id(component_id)

    @transaction.atomic()
    def update_component_graph(self, graph, title, promql, sequence):
        data = {
            "title": title,
            "promql": self.add_or_update_label(graph.component_id, promql),
        }
        if sequence != graph.sequence:
            data["sequence"] = sequence
        self._sequence_move_back(graph.component_id, sequence, graph.sequence)
        component_graph_repo.update(graph.component_id, graph.graph_id, **data)
        return component_graph_repo.get(graph.component_id, graph.graph_id).to_dict()

    def add_or_update_label(self, component_id, promql):
        """
        Add service_id label, or replace illegal service_id label
        """
        promql_parser = BASE_DIR + "/bin/" + platform.system().lower() + "/promql-parser"
        c = subprocess.Popen([os.getenv("PROMQL_PARSER", promql_parser), "--promql", promql, "--component_id", component_id],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        new_promql, err = c.communicate()
        if err != "":
            logger.warning("ensure service id for promql({}): {}".format(promql, err))
            raise AbortRequest("invalid promql", "非法的 prometheus 查询语句")

        return new_promql

    def bulk_create(self, component_id, graphs):
        if not graphs:
            return
        cgs = []
        for graph in graphs:
            try:
                promql = self.add_or_update_label(component_id, graph.get("promql"))
            except AbortRequest as e:
                logger.warning("promql: {}, {}".format(graph.get("promql"), e))
                continue
            cgs.append(
                ComponentGraph(
                    component_id=component_id,
                    graph_id=make_uuid(),
                    title=graph.get("title"),
                    promql=promql,
                    sequence=graph.get("sequence"),
                ))
        ComponentGraph.objects.bulk_create(cgs)

    @staticmethod
    def _next_sequence(component_id):
        graphs = component_graph_repo.list(component_id=component_id)
        if not graphs:
            return 0
        sequences = [graph.sequence for graph in graphs]
        sequences.sort()
        return sequences[len(sequences) - 1] + 1

    @staticmethod
    def _sequence_move_forward(component_id, sequence):
        graphs = component_graph_repo.list_gt_sequence(component_id=component_id, sequence=sequence)
        for graph in graphs:
            graph.sequence -= 1
            graph.save()

    @staticmethod
    def _sequence_move_back(component_id, left_sequence, right_sequence):
        graphs = component_graph_repo.list_between_sequence(
            component_id=component_id, left_sequence=left_sequence, right_sequence=right_sequence)
        for graph in graphs:
            graph.sequence += 1
            graph.save()


component_graph_service = ComponentGraphService()

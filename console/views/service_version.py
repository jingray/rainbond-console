# -*- coding: utf8 -*-
"""
  Created on 2018/6/21.
"""
import logging
import operator

from django.views.decorators.cache import never_cache
from rest_framework.response import Response

from console.utils.timeutil import current_time_str
from console.views.app_config.base import AppBaseView
from www.apiclient.regionapi import RegionInvokeApi
from www.decorator import perm_required
from www.utils.return_message import general_message, error_message
from console.repositories.event_repo import event_repo
from django.core.paginator import Paginator


logger = logging.getLogger("default")

region_api = RegionInvokeApi()

BUILD_KIND_MAP = {
    "build_from_source_code": "源码构建",
    "build_from_image": "镜像构建",
    "build_from_market_image": "云市镜像构建",
    "build_from_market_slug": "云市slug包构建"
}


class AppVersionsView(AppBaseView):
    @never_cache
    @perm_required('view_service')
    def get(self, request, *args, **kwargs):
        """
        获取服务的构建版本
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path
        """
        try:
            page = request.GET.get("page_num", 1)
            page_size = request.GET.get("page_size", 10)
            body = region_api.get_service_build_versions(self.response_region, self.tenant.tenant_name,
                                                         self.service.service_alias)
            build_version_sort = body["list"]
            build_version_sort.sort(key=operator.itemgetter('BuildVersion'), reverse=True)
            paginator = Paginator(build_version_sort, page_size)
            build_version_list = paginator.page(int(page)).object_list

            events = event_repo.get_events_before_specify_time(self.tenant.tenant_id, self.service.service_id,
                                                               current_time_str(fmt="%Y-%m-%d %H:%M:%S")).filter(type="deploy")
            version_user_map = {event.deploy_version: event.user_name for event in events}

            versions_info = build_version_list
            version_list = []
            for info in versions_info:
                version_list.append({
                    "build_version": info["BuildVersion"],
                    "kind": BUILD_KIND_MAP.get(info["Kind"]),
                    "service_type": info["DeliveredType"],
                    "image_url": info["ImageName"],
                    "repo_url": info["RepoURL"],
                    "commit_msg": info["CommitMsg"],
                    "author": info["Author"],
                    "create_time": info["CreatedAt"],
                    "status": info["FinalStatus"],
                    "build_user": version_user_map.get(info["BuildVersion"], "未知")
                })
            res_versions = sorted(version_list,
                                  key=lambda version: version["build_version"], reverse=True)
            # try:
            #     result = paginator.page(page).object_list
            # except PageNotAnInteger:
            #     result = paginator.page(1).object_list
            # except EmptyPage:
            #     result = paginator.page(paginator.num_pages).object_list
            result = general_message(200, "success", "查询成功", list=res_versions, total=paginator.count)
            return Response(result, status=result["code"])
        except Exception as e:
            result = error_message(e.message)
            return Response(result, status=500)


class AppVersionManageView(AppBaseView):
    @never_cache
    @perm_required('manage_service_config')
    def delete(self, request, *args, **kwargs):
        """
        删除应用的某次构建版本
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path
            - name: version_id
              description: 版本ID
              required: true
              type: string
              paramType: path

        """
        version_id = kwargs.get("version_id", None)
        try:
            if not version_id:
                return Response(general_message(400, "attr_name not specify", u"请指定需要删除的具体版本"))
            region_api.delete_service_build_version(self.response_region, self.tenant.tenant_name,
                                                    self.service.service_alias, version_id)
            # event_repo.delete_event_by_build_version(self.service.service_id, version_id)
            result = general_message(200, "success", u"删除成功")
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])

    @never_cache
    @perm_required('view_service')
    def get(self, request, *args, **kwargs):
        """
        获取应用的某个具体版本
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path
            - name: version_id
              description: 版本id
              required: true
              type: string
              paramType: path

        """
        version_id = kwargs.get("version_id", None)
        try:
            if not version_id:
                return Response(general_message(400, "attr_name not specify", u"请指定需要查询的具体版本"))

            res, body = region_api.get_service_build_version_by_id(self.response_region, self.tenant.tenant_name,
                                                                   self.service.service_alias, version_id)
            data = body['bean']

            result = general_message(200, "success", u"查询成功", bean={"is_exist": data["status"]})
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])

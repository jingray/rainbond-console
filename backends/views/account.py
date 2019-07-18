# -*- coding: utf8 -*-

import logging
import os

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from backends.services.enterpriseservice import enterprise_service
from backends.services.resultservice import *
from backends.services.userservice import user_service
from backends.views.base import BaseAPIView
from console.views.base import AlowAnyApiView
from www.apiclient.baseclient import client_auth_service
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User as TokenAuthUser
from console.services.user_services import user_services
from console.repositories.enterprise_repo import enterprise_repo
from console.repositories.user_repo import user_repo
from console.services.enterprise_services import enterprise_services
from backends.services.authservice import auth_service

logger = logging.getLogger("default")


class AccountCreateView(BaseAPIView):
    def post(self, request, *args, **kwargs):
        """
        管理后台初始化云帮账户（deprecated）

        ---
        parameters:
            - name: body
              description: json内容
              required: true
              type: string
              paramType: body

        """
        result = {}
        try:
            user_info = request.data.get("user_info")
            enterprise_info = request.data.get("enterprise_info")
            username = user_info["username"]
            password = user_info["password"]
            email = user_info["email"]
            phone = user_info["phone"]
            eid = enterprise_info["eid"]
            name = enterprise_info["name"]
            is_active = enterprise_info["is_active"]
            logger.debug("user info {0} enterprise info {1}".format(user_info, enterprise_info))
            is_user_exist = user_service.is_user_exist(username)
            if is_user_exist:
                result = generate_result("1002", "user exist", "用户已存在")
                return Response(result)
            if_ent_exist = enterprise_service.is_enterprise_exist(name)
            if if_ent_exist:
                result = generate_result("1004", "exterprise exist", "企业已存在")
                return Response(result)
            logger.debug("create tenant enterprise")
            # 创建企业
            enterprise = enterprise_service.create_enterprise(eid, name, name, "", is_active)
            # 创建用户
            logger.debug("create tenant user")
            user = user_service.create_user(username, password, email or '', phone or '', enterprise.enterprise_id, "backend")
            logger.debug("create tenant and init tenant")
            user.is_active = True
            user.save()
            result = generate_result("0000", "success", "初始化成功")

        except Exception as e:
            logger.exception(e)
            result = generate_error_result()
        return Response(result)


class TenantEnterpriseView(BaseAPIView):
    def put(self, request, enterprise_id, *args, **kwargs):
        """
        更新企业信息
        ---
        parameters:
            - name: enterprise_id
              description: 企业ID
              required: true
              type: string
              paramType: path
            - name: market_client_id
              description: 云市客户端id
              required: true
              type: string
              paramType: form
            - name: market_client_token
              description: 云市客户端token
              required: true
              type: string
              paramType: form
        """
        try:
            market_client_id = request.data.get("market_client_id")
            market_client_token = request.data.get("market_client_token")
            domain = os.getenv('GOODRAIN_APP_API', settings.APP_SERVICE_API["url"])
            is_success = client_auth_service.save_market_access_token(enterprise_id, domain, market_client_id,
                                                                      market_client_token)
            if is_success:
                result = generate_result("0000", "success", "企业{0}信息更新成功".format(enterprise_id))
            else:
                result = generate_result("7878", "enterprise not exist", "企业{0} 信息不存在".format(enterprise_id))
        except Exception as e:
            logger.exception(e)
            result = generate_error_result()
        return Response(result)


class EnterpriseFuzzyQueryView(BaseAPIView):
    def get(self, request, *args, **kwargs):
        """
        模糊查询企业信息
        ---
        parameters:
            - name: enterprise_alias
              description: 企业别名
              required: false
              type: string
              paramType: form
            - name: enterprise_name
              description: 企业名称
              required: false
              type: string
              paramType: form
        """
        try:
            enterprise_alias = request.GET.get("enterprise_alias", None)
            enterprise_name = request.GET.get("enterprise_name", None)
            enters = []
            if enterprise_alias:
                enters = enterprise_service.fuzzy_query_enterprise_by_enterprise_alias(enterprise_alias)
            if enterprise_name:
                enters = enterprise_service.fuzzy_query_enterprise_by_enterprise_name(enterprise_name)

            rt_enterprises = [{
                "enterprise_id": enter.enterprise_id,
                "enterprise_name": enter.enterprise_name,
                "enterprise_alias": enter.enterprise_alias
            } for enter in enters]
            result = generate_result("0000", "success", "查询成功", list=rt_enterprises)
        except Exception as e:
            logger.exception(e)
            result = generate_error_result()
        return Response(result)


class AuthAccessTokenView(AlowAnyApiView):
    def post(self, request, *args, **kwargs):
        """
        back manager get access token for console
        ---
        parameters:
            - name: username
              description: 用户名
              required: true
              type: string
              paramType: path
            - name: password
              description: 密码
              required: true
              type: string
              paramType: form
            - name: enterprise_id
              description: 企业ID
              required: true
              type: string
              paramType: form
            - name: enterprise_alias
              description: 企业别名
              required: true
              type: string
              paramType: form
        """
        try:
            auth = request.data.get('Authorization', '')
            if auth != settings.MANAGE_SECRET_KEY:
                return Response(generate_result("0401", "authorization error", "验证未通过"))

            enterprise_alias = request.data.get("enterprise_alias", None)
            # 校验参数
            if not enterprise_alias:
                return Response(generate_result("1003", "params error", "参数错误"))
            # 查询企业信息

            enterprise = enterprise_services.get_enterprise_by_enterprise_alias(enterprise_alias)
            logger.debug('----------type----------->{0}'.format(type(enterprise)))

            if not enterprise:
                return Response(generate_result("1005", "enterprise already exists", "当前企业在控制台不存在"))
            # 获取企业第一个用户（即企业管理员）
            users = user_repo.get_enterprise_users(enterprise.enterprise_id).order_by("user_id")
            if not users:
                return Response(generate_result("1007", "is not enterprise admin", "无企业管理员"))
            admin_user = users[0]
            token = auth_service.create_token_auth_user(admin_user.nick_name, admin_user.password)
            bean = {
                "console_access_token": token.key,
                "enterprise_info": enterprise.to_dict(),
                "user_info": admin_user.to_dict()
            }

            result = generate_result("0000", "success", "信息获取成功", bean=bean)

        except Exception as e:
            logger.exception(e)
            result = generate_error_result()
        return Response(result)


class EnterpriseInitView(AlowAnyApiView):
    def post(self, request, *args, **kwargs):

        try:
            logger.debug('=============>{}')
            auth = request.data.get('Authorization', '')
            logger.debug('=============>{0}'.format(auth))
            if auth != settings.MANAGE_SECRET_KEY:
                return Response(generate_result("0401", "authorization error", "验证未通过"))
            enterprise_info = enterprise_repo.get_enterprise_first()
            result = generate_result("0000", "success", "信息获取成功", bean=enterprise_info.to_dict())
        except Exception as e:
            logger.exception(e)
            result = generate_error_result()
        return Response(result)

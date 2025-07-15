# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3
from botocore.exceptions import ClientError


def create_config_for_servicenow(secret_arn, instance):



    """Function create_config_for_servicenow."""




    """Function create_config_for_servicenow."""

    """
    Create ServiceNow configuration for Q Business data source
    
    Args:
        secret_arn (str): ARN of the secret containing credentials
        instance (str): ServiceNow instance name
        
    Returns:
        dict: ServiceNow configuration
    """
    return {
        "connectionConfiguration": {
            "repositoryEndpointMetadata": {
                "hostUrl": f"{instance}.service-now.com",
                "authType": "OAuth2",
                "servicenowInstanceVersion": "Others",
            },
            # No hardcoded credentials - using secret_arn instead
        },
        "enableIdentityCrawler": "true",
        "crawlType": "FULL_CRAWL",
        "version": "1.0.0",
        "syncMode": "FORCED_FULL_CRAWL",
        "type": "SERVICENOW",
        "secretArn": f"{secret_arn}",
        "additionalProperties": {
            "maxFileSizeInMegaBytes": "50",
            "isCrawlKnowledgeArticle": "true",
            "isCrawlKnowledgeArticleAttachment": "true",
            "includePublicArticlesOnly": "false",
            "knowledgeArticleFilter": "active=true",
            "isCrawlServiceCatalog": "true",
            "isCrawlServiceCatalogAttachment": "true",
            "isCrawlActiveServiceCatalog": "true",
            "isCrawlInactiveServiceCatalog": "true",
            "isCrawlIncident": "false",
            "isCrawlIncidentAttachment": "true",
            "isCrawlActiveIncident": "false",
            "isCrawlInactiveIncident": "false",
            "applyACLForKnowledgeArticle": "true",
            "applyACLForServiceCatalog": "true",
            "applyACLForIncident": "true",
            "incidentStateType": ["Open", "Open - Unassigned", "Resolved", "All"],
            "knowledgeArticleTitleRegExp": "",
            "serviceCatalogTitleRegExp": "",
            "incidentTitleRegExp": "",
            "inclusionFileTypePatterns": [],
            "exclusionFileTypePatterns": [],
            "inclusionFileNamePatterns": [],
            "exclusionFileNamePatterns": [],
        },
        "repositoryConfigurations": {
            "knowledgeArticle": {
                "fieldMappings": [
                    {"indexFieldName": "sn_ka_text", "indexFieldType": "STRING", "dataSourceFieldName": "text"},
                    {
                        "indexFieldName": "sn_ka_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "description",
                    },
                    {
                        "indexFieldName": "sn_ka_short_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "short_description",
                    },
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_created_on",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_updated_on",
                    },
                    {
                        "indexFieldName": "_category",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "kb_category_name",
                    },
                    {
                        "indexFieldName": "_authors",
                        "indexFieldType": "STRING_LIST",
                        "dataSourceFieldName": "sys_created_by",
                    },
                    {
                        "indexFieldName": "sn_updatedBy",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_updated_by",
                    },
                    {"indexFieldName": "sn_sys_id", "indexFieldType": "STRING", "dataSourceFieldName": "sys_id"},
                    {
                        "indexFieldName": "sn_ka_publish_date",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "published",
                    },
                    {
                        "indexFieldName": "sn_ka_workflow_state",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "workflow_state",
                    },
                    {
                        "indexFieldName": "sn_ka_category",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "kb_category",
                    },
                    {
                        "indexFieldName": "sn_ka_article_type",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "article_type",
                    },
                    {
                        "indexFieldName": "sn_ka_first_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "first_name",
                    },
                    {
                        "indexFieldName": "sn_ka_last_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "last_name",
                    },
                    {
                        "indexFieldName": "sn_ka_user_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "user_name",
                    },
                    {
                        "indexFieldName": "sn_ka_valid_to",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "valid_to",
                    },
                    {
                        "indexFieldName": "sn_ka_knowledge_base",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "kb_knowledge_base",
                    },
                    {"indexFieldName": "sn_ka_number", "indexFieldType": "STRING", "dataSourceFieldName": "number"},
                    {"indexFieldName": "sn_url", "indexFieldType": "STRING", "dataSourceFieldName": "url"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "displayUrl"},
                    {
                        "indexFieldName": "sn_ka_display_attachments",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "display_attachments",
                    },
                    {"indexFieldName": "sn_ka_roles", "indexFieldType": "STRING", "dataSourceFieldName": "roles"},
                    {"indexFieldName": "sn_ka_wiki", "indexFieldType": "STRING", "dataSourceFieldName": "wiki"},
                    {"indexFieldName": "sn_ka_rating", "indexFieldType": "STRING", "dataSourceFieldName": "rating"},
                    {"indexFieldName": "sn_ka_source", "indexFieldType": "STRING", "dataSourceFieldName": "source"},
                    {
                        "indexFieldName": "sn_ka_disable_suggesting",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "disable_suggesting",
                    },
                    {
                        "indexFieldName": "sn_ka_use_count",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "use_count",
                    },
                    {"indexFieldName": "sn_ka_flagged", "indexFieldType": "STRING", "dataSourceFieldName": "flagged"},
                    {
                        "indexFieldName": "sn_ka_disable_commenting",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "disable_commenting",
                    },
                    {"indexFieldName": "sn_ka_retired", "indexFieldType": "STRING", "dataSourceFieldName": "retired"},
                    {"indexFieldName": "sn_ka_image", "indexFieldType": "STRING", "dataSourceFieldName": "image"},
                    {"indexFieldName": "sn_ka_author", "indexFieldType": "STRING", "dataSourceFieldName": "author"},
                    {"indexFieldName": "sn_ka_active", "indexFieldType": "STRING", "dataSourceFieldName": "active"},
                    {
                        "indexFieldName": "sn_ka_helpful_count",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "helpful_count",
                    },
                    {
                        "indexFieldName": "sn_ka_replacement_article",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "replacement_article",
                    },
                    {
                        "indexFieldName": "sn_ka_meta_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "meta_description",
                    },
                    {
                        "indexFieldName": "sn_ka_taxonomy_topic",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "taxonomy_topic",
                    },
                    {"indexFieldName": "sn_ka_meta", "indexFieldType": "STRING", "dataSourceFieldName": "meta"},
                    {
                        "indexFieldName": "sn_ka_view_as_allowed",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "view_as_allowed",
                    },
                    {"indexFieldName": "sn_ka_topic", "indexFieldType": "STRING", "dataSourceFieldName": "topic"},
                ]
            },
            "attachment": {
                "fieldMappings": [
                    {"indexFieldName": "sn_sys_id", "indexFieldType": "STRING", "dataSourceFieldName": "sys_id"},
                    {"indexFieldName": "sn_file_size", "indexFieldType": "LONG", "dataSourceFieldName": "size_bytes"},
                    {"indexFieldName": "sn_file_name", "indexFieldType": "STRING", "dataSourceFieldName": "file_name"},
                    {
                        "indexFieldName": "sn_sys_mod_count",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_mod_count",
                    },
                    {
                        "indexFieldName": "sn_average_image_color",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "average_image_color",
                    },
                    {
                        "indexFieldName": "sn_image_width",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "image_width",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_updated_on",
                    },
                    {"indexFieldName": "sn_sys_tags", "indexFieldType": "STRING", "dataSourceFieldName": "sys_tags"},
                    {
                        "indexFieldName": "sn_table_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "table_name",
                    },
                    {
                        "indexFieldName": "sn_image_height",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "image_height",
                    },
                    {
                        "indexFieldName": "sn_updatedBy",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_updated_by",
                    },
                    {
                        "indexFieldName": "sn_content_type",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "content_type",
                    },
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_created_on",
                    },
                    {
                        "indexFieldName": "sn_size_compressed",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "size_compressed",
                    },
                    {
                        "indexFieldName": "sn_compressed",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "compressed",
                    },
                    {"indexFieldName": "sn_state", "indexFieldType": "STRING", "dataSourceFieldName": "state"},
                    {
                        "indexFieldName": "sn_table_sys_id",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "table_sys_id",
                    },
                    {
                        "indexFieldName": "sn_chunk_size_bytes",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "chunk_size_bytes",
                    },
                    {"indexFieldName": "sn_hash", "indexFieldType": "STRING", "dataSourceFieldName": "hash"},
                    {
                        "indexFieldName": "_authors",
                        "indexFieldType": "STRING_LIST",
                        "dataSourceFieldName": "sys_created_by",
                    },
                    {"indexFieldName": "sn_url", "indexFieldType": "STRING", "dataSourceFieldName": "url"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "displayUrl"},
                ]
            },
            "serviceCatalog": {
                "fieldMappings": [
                    {"indexFieldName": "sn_sys_id", "indexFieldType": "STRING", "dataSourceFieldName": "sys_id"},
                    {
                        "indexFieldName": "sn_sc_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "description",
                    },
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_created_on",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_updated_on",
                    },
                    {
                        "indexFieldName": "_authors",
                        "indexFieldType": "STRING_LIST",
                        "dataSourceFieldName": "sys_created_by",
                    },
                    {
                        "indexFieldName": "sn_updatedBy",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_updated_by",
                    },
                    {"indexFieldName": "_category", "indexFieldType": "STRING", "dataSourceFieldName": "category_name"},
                    {
                        "indexFieldName": "sn_sc_catalogs",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sc_catalogs",
                    },
                    {
                        "indexFieldName": "sn_sc_catalogs_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sc_catalogs_name",
                    },
                    {"indexFieldName": "sn_sc_category", "indexFieldType": "STRING", "dataSourceFieldName": "category"},
                    {
                        "indexFieldName": "sn_sc_category_full_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "category_full_name",
                    },
                    {"indexFieldName": "sn_url", "indexFieldType": "STRING", "dataSourceFieldName": "url"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "displayUrl"},
                    {
                        "indexFieldName": "sn_sc_show_var_help_on_load",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "show_variable_help_on_load",
                    },
                    {
                        "indexFieldName": "sn_sc_no_order_now",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_order_now",
                    },
                    {
                        "indexFieldName": "sn_sc_sc_ic_version",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sc_ic_version",
                    },
                    {
                        "indexFieldName": "sn_sc_delivery_time",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "delivery_time",
                    },
                    {
                        "indexFieldName": "sn_sc_published_ref",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "published_ref",
                    },
                    {"indexFieldName": "sn_sc_price", "indexFieldType": "STRING", "dataSourceFieldName": "price"},
                    {
                        "indexFieldName": "sn_sc_recurring_frequency",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "recurring_frequency",
                    },
                    {"indexFieldName": "sn_sc_sys_name", "indexFieldType": "STRING", "dataSourceFieldName": "sys_name"},
                    {"indexFieldName": "sn_sc_model", "indexFieldType": "STRING", "dataSourceFieldName": "model"},
                    {"indexFieldName": "sn_sc_state", "indexFieldType": "STRING", "dataSourceFieldName": "state"},
                    {"indexFieldName": "sn_sc_no_cart", "indexFieldType": "STRING", "dataSourceFieldName": "no_cart"},
                    {"indexFieldName": "sn_sc_group", "indexFieldType": "STRING", "dataSourceFieldName": "group"},
                    {"indexFieldName": "sn_sc_hide_sp", "indexFieldType": "STRING", "dataSourceFieldName": "hide_sp"},
                    {"indexFieldName": "sn_sc_order", "indexFieldType": "STRING", "dataSourceFieldName": "order"},
                    {
                        "indexFieldName": "sn_sc_start_closed",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "start_closed",
                    },
                    {"indexFieldName": "sn_sc_image", "indexFieldType": "STRING", "dataSourceFieldName": "image"},
                    {
                        "indexFieldName": "sn_sc_no_quantity",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_quantity",
                    },
                    {
                        "indexFieldName": "sn_sc_delivery_plan",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "delivery_plan",
                    },
                    {"indexFieldName": "sn_sc_active", "indexFieldType": "STRING", "dataSourceFieldName": "active"},
                    {
                        "indexFieldName": "sn_sc_checked_out",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "checked_out",
                    },
                    {
                        "indexFieldName": "sn_sc_custom_cart",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "custom_cart",
                    },
                    {
                        "indexFieldName": "sn_sc_no_cart_v2",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_cart_v2",
                    },
                    {
                        "indexFieldName": "sn_sc_no_proceed_checkout",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_proceed_checkout",
                    },
                    {
                        "indexFieldName": "sn_sc_ignore_price",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "ignore_price",
                    },
                    {
                        "indexFieldName": "sn_sc_sys_update_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_update_name",
                    },
                    {"indexFieldName": "sn_sc_meta", "indexFieldType": "STRING", "dataSourceFieldName": "meta"},
                    {
                        "indexFieldName": "sn_sc_omit_price",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "omit_price",
                    },
                    {"indexFieldName": "sn_sc_name", "indexFieldType": "STRING", "dataSourceFieldName": "name"},
                    {
                        "indexFieldName": "sn_sc_mobile_hide_price",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "mobile_hide_price",
                    },
                    {
                        "indexFieldName": "sn_sc_no_wishlist_v2",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_wishlist_v2",
                    },
                    {"indexFieldName": "sn_sc_preview", "indexFieldType": "STRING", "dataSourceFieldName": "preview"},
                    {"indexFieldName": "sn_sc_type", "indexFieldType": "STRING", "dataSourceFieldName": "type"},
                    {
                        "indexFieldName": "sn_sc_access_type",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "access_type",
                    },
                    {"indexFieldName": "sn_sc_roles", "indexFieldType": "STRING", "dataSourceFieldName": "roles"},
                    {"indexFieldName": "sn_sc_icon", "indexFieldType": "STRING", "dataSourceFieldName": "icon"},
                    {
                        "indexFieldName": "sn_sc_mobile_picture",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "mobile_picture",
                    },
                    {
                        "indexFieldName": "sn_sc_short_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "short_description",
                    },
                    {
                        "indexFieldName": "sn_sc_availability",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "availability",
                    },
                    {
                        "indexFieldName": "sn_sc_mandatory_attachment",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "mandatory_attachment",
                    },
                    {
                        "indexFieldName": "sn_sc_request_method",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "request_method",
                    },
                    {
                        "indexFieldName": "sn_sc_visible_guide",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "visible_guide",
                    },
                    {
                        "indexFieldName": "sn_sc_visible_standalone",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "visible_standalone",
                    },
                    {"indexFieldName": "sn_sc_no_order", "indexFieldType": "STRING", "dataSourceFieldName": "no_order"},
                    {"indexFieldName": "sn_sc_vendor", "indexFieldType": "STRING", "dataSourceFieldName": "vendor"},
                    {
                        "indexFieldName": "sn_sc_no_attachment_v2",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_attachment_v2",
                    },
                    {
                        "indexFieldName": "sn_sc_mobile_picture_type",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "mobile_picture_type",
                    },
                    {
                        "indexFieldName": "sn_sc_visible_bundle",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "visible_bundle",
                    },
                    {
                        "indexFieldName": "sn_sc_ordered_item_link",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "ordered_item_link",
                    },
                    {"indexFieldName": "sn_sc_owner", "indexFieldType": "STRING", "dataSourceFieldName": "owner"},
                    {
                        "indexFieldName": "sn_sc_no_delivery_time_v2",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_delivery_time_v2",
                    },
                    {"indexFieldName": "sn_sc_cost", "indexFieldType": "STRING", "dataSourceFieldName": "cost"},
                    {
                        "indexFieldName": "sn_sc_no_quantity_v2",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "no_quantity_v2",
                    },
                    {
                        "indexFieldName": "sn_sc_recurring_price",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "recurring_price",
                    },
                    {
                        "indexFieldName": "sn_sc_list_price",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "list_price",
                    },
                    {"indexFieldName": "sn_sc_sys_tags", "indexFieldType": "STRING", "dataSourceFieldName": "sys_tags"},
                    {"indexFieldName": "sn_sc_billable", "indexFieldType": "STRING", "dataSourceFieldName": "billable"},
                    {"indexFieldName": "sn_sc_picture", "indexFieldType": "STRING", "dataSourceFieldName": "picture"},
                    {
                        "indexFieldName": "sn_sc_display_price_property",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "display_price_property",
                    },
                    {
                        "indexFieldName": "sn_sc_taxonomy_topic",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "taxonomy_topic",
                    },
                    {
                        "indexFieldName": "sn_sc_delivery_plan_script",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "delivery_plan_script",
                    },
                    {"indexFieldName": "sn_sc_location", "indexFieldType": "STRING", "dataSourceFieldName": "location"},
                ]
            },
            "incident": {
                "fieldMappings": [
                    {"indexFieldName": "sn_inc_sys_id", "indexFieldType": "STRING", "dataSourceFieldName": "sys_id"},
                    {
                        "indexFieldName": "sn_inc_short_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "short_description",
                    },
                    {
                        "indexFieldName": "sn_inc_description",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "description",
                    },
                    {
                        "indexFieldName": "_authors",
                        "indexFieldType": "STRING_LIST",
                        "dataSourceFieldName": "sys_created_by",
                    },
                    {
                        "indexFieldName": "_created_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_created_on",
                    },
                    {
                        "indexFieldName": "_last_updated_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sys_updated_on",
                    },
                    {
                        "indexFieldName": "sn_updatedBy",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_updated_by",
                    },
                    {"indexFieldName": "sn_inc_number", "indexFieldType": "STRING", "dataSourceFieldName": "number"},
                    {
                        "indexFieldName": "sn_inc_opened_by",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "opened_by",
                    },
                    {"indexFieldName": "sn_inc_state", "indexFieldType": "STRING", "dataSourceFieldName": "state"},
                    {
                        "indexFieldName": "sn_inc_business_impact",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "business_impact",
                    },
                    {"indexFieldName": "sn_inc_impact", "indexFieldType": "STRING", "dataSourceFieldName": "impact"},
                    {
                        "indexFieldName": "sn_inc_priority",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "priority",
                    },
                    {"indexFieldName": "sn_inc_urgency", "indexFieldType": "STRING", "dataSourceFieldName": "urgency"},
                    {
                        "indexFieldName": "sn_inc_opened_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "opened_at",
                    },
                    {
                        "indexFieldName": "sn_inc_business_duration",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "business_duration",
                    },
                    {
                        "indexFieldName": "sn_inc_caller_id",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "caller_id",
                    },
                    {
                        "indexFieldName": "sn_inc_resolved_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "resolved_at",
                    },
                    {
                        "indexFieldName": "sn_inc_category",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "category",
                    },
                    {
                        "indexFieldName": "sn_inc_subcategory",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "subcategory",
                    },
                    {
                        "indexFieldName": "sn_inc_close_code",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "close_code",
                    },
                    {
                        "indexFieldName": "sn_inc_assignment_group",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "assignment_group",
                    },
                    {
                        "indexFieldName": "sn_inc_close_notes",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "close_notes",
                    },
                    {
                        "indexFieldName": "sn_inc_sys_class_name",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_class_name",
                    },
                    {
                        "indexFieldName": "sn_inc_parent_incident",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "parent_incident",
                    },
                    {
                        "indexFieldName": "sn_inc_incident_state",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "incident_state",
                    },
                    {"indexFieldName": "sn_inc_company", "indexFieldType": "STRING", "dataSourceFieldName": "company"},
                    {
                        "indexFieldName": "sn_inc_assigned_to",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "assigned_to",
                    },
                    {
                        "indexFieldName": "sn_inc_hold_reason",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "hold_reason",
                    },
                    {
                        "indexFieldName": "sn_inc_work_notes",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "work_notes",
                    },
                    {
                        "indexFieldName": "sn_inc_comments_and_work_notes",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "comments_and_work_notes",
                    },
                    {
                        "indexFieldName": "sn_inc_work_notes_list",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "work_notes_list",
                    },
                    {
                        "indexFieldName": "sn_inc_comments",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "comments",
                    },
                    {"indexFieldName": "sn_url", "indexFieldType": "STRING", "dataSourceFieldName": "url"},
                    {"indexFieldName": "_source_uri", "indexFieldType": "STRING", "dataSourceFieldName": "displayUrl"},
                    {"indexFieldName": "sn_inc_active", "indexFieldType": "STRING", "dataSourceFieldName": "active"},
                    {
                        "indexFieldName": "sn_inc_activity_due",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "activity_due",
                    },
                    {
                        "indexFieldName": "sn_inc_additional_assign_list",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "additional_assignee_list",
                    },
                    {
                        "indexFieldName": "sn_inc_approval",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "approval",
                    },
                    {
                        "indexFieldName": "sn_inc_approval_history",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "approval_history",
                    },
                    {
                        "indexFieldName": "sn_inc_approval_set",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "approval_set",
                    },
                    {
                        "indexFieldName": "sn_inc_business_service",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "business_service",
                    },
                    {
                        "indexFieldName": "sn_inc_closed_by",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "closed_by",
                    },
                    {"indexFieldName": "sn_inc_cmdb_ci", "indexFieldType": "STRING", "dataSourceFieldName": "cmdb_ci"},
                    {
                        "indexFieldName": "sn_inc_resolved_by",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "resolved_by",
                    },
                    {
                        "indexFieldName": "sn_inc_sys_domain",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "sys_domain",
                    },
                    {
                        "indexFieldName": "sn_inc_business_stc",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "business_stc",
                    },
                    {
                        "indexFieldName": "sn_inc_calendar_duration",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "calendar_duration",
                    },
                    {
                        "indexFieldName": "sn_inc_calendar_stc",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "calendar_stc",
                    },
                    {"indexFieldName": "sn_inc_cause", "indexFieldType": "STRING", "dataSourceFieldName": "cause"},
                    {
                        "indexFieldName": "sn_inc_caused_by",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "caused_by",
                    },
                    {
                        "indexFieldName": "sn_inc_child_incidents",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "child_incidents",
                    },
                    {
                        "indexFieldName": "sn_inc_closed_at",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "closed_at",
                    },
                    {
                        "indexFieldName": "sn_inc_contact_type",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "contact_type",
                    },
                    {
                        "indexFieldName": "sn_inc_contract",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "contract",
                    },
                    {
                        "indexFieldName": "sn_inc_correlation_display",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "correlation_display",
                    },
                    {
                        "indexFieldName": "sn_inc_delivery_plan",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "delivery_plan",
                    },
                    {
                        "indexFieldName": "sn_inc_delivery_task",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "delivery_task",
                    },
                    {
                        "indexFieldName": "sn_inc_due_date",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "due_date",
                    },
                    {
                        "indexFieldName": "sn_inc_escalation",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "escalation",
                    },
                    {
                        "indexFieldName": "sn_inc_expected_start",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "expected_start",
                    },
                    {
                        "indexFieldName": "sn_inc_follow_up",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "follow_up",
                    },
                    {
                        "indexFieldName": "sn_inc_group_list",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "group_list",
                    },
                    {
                        "indexFieldName": "sn_inc_knowledge",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "knowledge",
                    },
                    {
                        "indexFieldName": "sn_inc_location",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "location",
                    },
                    {
                        "indexFieldName": "sn_inc_made_sla",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "made_sla",
                    },
                    {"indexFieldName": "sn_inc_notify", "indexFieldType": "STRING", "dataSourceFieldName": "notify"},
                    {"indexFieldName": "sn_inc_order", "indexFieldType": "STRING", "dataSourceFieldName": "order"},
                    {
                        "indexFieldName": "sn_inc_origin_id",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "origin_id",
                    },
                    {
                        "indexFieldName": "sn_inc_origin_table",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "origin_table",
                    },
                    {"indexFieldName": "sn_inc_parent", "indexFieldType": "STRING", "dataSourceFieldName": "parent"},
                    {
                        "indexFieldName": "sn_inc_problem_id",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "problem_id",
                    },
                    {
                        "indexFieldName": "sn_inc_reassignment_count",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "reassignment_count",
                    },
                    {
                        "indexFieldName": "sn_inc_reopen_count",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "reopen_count",
                    },
                    {
                        "indexFieldName": "sn_inc_reopened_by",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "reopened_by",
                    },
                    {
                        "indexFieldName": "sn_inc_reopened_time",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "reopened_time",
                    },
                    {"indexFieldName": "sn_inc_rfc", "indexFieldType": "STRING", "dataSourceFieldName": "rfc"},
                    {
                        "indexFieldName": "sn_inc_route_reason",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "route_reason",
                    },
                    {
                        "indexFieldName": "sn_inc_service_offering",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "service_offering",
                    },
                    {
                        "indexFieldName": "sn_inc_severity",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "severity",
                    },
                    {
                        "indexFieldName": "sn_inc_sla_due",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "sla_due",
                    },
                    {
                        "indexFieldName": "sn_inc_task_effective_number",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "task_effective_number",
                    },
                    {
                        "indexFieldName": "sn_inc_time_worked",
                        "indexFieldType": "DATE",
                        "dateFieldFormat": "yyyy-MM-dd'T'HH:mm:ss'Z'",
                        "dataSourceFieldName": "time_worked",
                    },
                    {
                        "indexFieldName": "sn_inc_universal_request",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "universal_request",
                    },
                    {
                        "indexFieldName": "sn_inc_upon_approval",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "upon_approval",
                    },
                    {
                        "indexFieldName": "sn_inc_upon_reject",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "upon_reject",
                    },
                    {
                        "indexFieldName": "sn_inc_user_input",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "user_input",
                    },
                    {
                        "indexFieldName": "sn_inc_watch_list",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "watch_list",
                    },
                    {
                        "indexFieldName": "sn_inc_work_end",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "work_end",
                    },
                    {
                        "indexFieldName": "sn_inc_work_start",
                        "indexFieldType": "STRING",
                        "dataSourceFieldName": "work_start",
                    },
                ]
            },
        },
    }


def create_data_source(application_id, index_id, configuration, datasource_name, role_arn):



    """Function create_data_source."""




    """Function create_data_source."""

    q = boto3.client("qbusiness")
    response = q.create_data_source(
        applicationId=application_id,
        indexId=index_id,
        displayName=datasource_name,
        configuration=configuration,
        syncSchedule="",
        roleArn=role_arn,
    )

    print(f"Data source creation response: {response}")
    return response


def store_credentials_in_secrets_manager(
    secret_name,
    username,
    password,
    client_id,
    client_secret,
    description="API credentials",
    region_name="us-east-1",
):



    """Function store_credentials_in_secrets_manager."""




    """Function store_credentials_in_secrets_manager."""

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    # Create the secret value as a JSON string
    secret_value = json.dumps(
        {"clientId": client_id, "clientSecret": client_secret, "username": username, "password": password}
    )
    try:
        # Create the secret in AWS Secrets Manager
        response = client.create_secret(Name=secret_name, Description=description, SecretString=secret_value)
        print(f"Secret {secret_name} successfully created/updated")
        return response
    except ClientError as e:
        # Handle specific errors
        if e.response["Error"]["Code"] == "ResourceExistsException":
            # Secret already exists, update it
            response = client.update_secret(SecretId=secret_name, SecretString=secret_value)
            print(f"Secret {secret_name} already existed and was updated")
            return response
        else:
            # Handle other exceptions
            print(f"Error: {e}")
            raise


def handler(event, context):



    """Function handler."""




    """Function handler."""

    print(f"received event {event}")
    data_source_name = event["body-json"]["datasourceName"]
    application_id = event["body-json"]["applicationId"]
    index_id = event["body-json"]["indexId"]
    instance = event["body-json"]["instance"]
    username = event["body-json"]["username"]
    password = event["body-json"]["password"]
    client_id = event["body-json"]["clientId"]
    client_secret = event["body-json"]["clientSecret"]

    secret_name = f"qbusiness-servicenow-secret-{instance}-{client_id}"
    secret_response = store_credentials_in_secrets_manager(secret_name, username, password, client_id, client_secret)

    config = create_config_for_servicenow(secret_response.get("ARN"), instance)
    print(f"config {config}")
    response = create_data_source(
        application_id, index_id, config, data_source_name, os.environ["DATA_SOURCE_ROLE_ARN"]
    )
    print(f"response: {response}")
    return {
        "statusCode": 200,
        "body": "QBusiness Data Source has been created",
        "response": {
            "dataSourceId": response["dataSourceId"],
            "applicationId": application_id,
            "indexId": index_id,
            "dataSourceName": data_source_name,
        },
    }


# For local testing only - will not run in Lambda
if __name__ == "__main__":
    # Test event for local development
    os.environ["DATA_SOURCE_ROLE_ARN"] = "arn:aws:iam::854174087803:role/snow-plugin-datasource-role"
    test_event = {
        "body-json": {
            "datasourceName": "connector-q-snow03",
            "applicationId": "app-id-placeholder",
            "indexId": "index-id-placeholder",
            "instance": "instance-name-placeholder",
            "username": "username-placeholder",
            "password": "password-placeholder",
            "clientId": "client-id-placeholder",
            "clientSecret": "client-secret-placeholder",
        }
    }
    handler(test_event, {})

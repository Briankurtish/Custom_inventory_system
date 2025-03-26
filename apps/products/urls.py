from django.urls import path
from .views import *

urlpatterns = [

    path(
        "add-batch/", add_batch_view, name="add-batch",
    ),
    path("batches/", ManageBatchView, name="batches"),
    path(
        "batch-logs/", BatchAuditLogView, name="batch-logs",
    ),
    path(
        "product-list/", ManageProductView, name="products",
    ),
    path(
        "product-logs/", ProductAuditLogView, name="product-logs",
    ),
    path(
        "add-product/", add_product_view, name="add-product",
    ),
    path("edit-batch/<int:pk>/", edit_batch_view, name="edit-batch"),  # Edit route

    path("edit-product/<int:pk>/", edit_product_view, name="edit-product"),
    path("edit-price/<int:pk>/", update_product_view, name="edit-price"),
    path("delete-product/<int:pk>/", delete_product_view, name="delete-product"),

    path("delete-batch/<int:pk>/", delete_batch_view, name="delete-batch"),

    path('get-brand-name/<int:generic_name_id>/', get_brand_name, name='get-brand-name'),

    path('fetch-brand-names/', fetch_brand_names, name='fetch_brand_names'),


    path(
        "add-dosage-form/", add_dosage_form_view, name="add-dosage-form",
    ),
    path("edit-dosage-form/<int:pk>/", edit_dosage_form_view, name="edit-dosage-form"),

    path("delete-dosage-form/<int:pk>/", delete_dosage_form_view, name="delete-dosage-form"),


    path(
        "add-dosage-type/", add_dosage_type_view, name="add-dosage-type",
    ),
    path("edit-dosage-type/<int:pk>/", edit_dosage_type_view, name="edit-dosage-type"),

    path("delete-dosage-type/<int:pk>/", delete_dosage_type_view, name="delete-dosage-type"),

    path('get-dosage-types/', get_dosage_types, name='get-dosage-types'),

    path('get-brand-and-batches/<int:generic_name_id>/', get_brand_and_batches, name='get_brand_and_batches'),

    path("product/<int:product_id>/history/", product_transaction_history, name="product_transaction_history"),
]

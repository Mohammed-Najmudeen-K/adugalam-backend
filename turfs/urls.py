from django.urls import path
from .views import (
    add_turf,
    turf_list,
    turf_detail,
    upload_turf_image,
    delete_turf_image,
    edit_turf,
    turf_search,
    turf_slots_by_date,
)

urlpatterns = [

    #  PUBLIC TURF APIs
    path("", turf_list),                                     # GET /turfs/
    path("<int:turf_id>/", turf_detail),                     # GET /turfs/5/
    path("search/", turf_search),                            # GET /turfs/search?q=football
    path("<int:turf_id>/slots/", turf_slots_by_date),        # GET /turfs/5/slots?date=YYYY-MM-DD

    # OWNER TURF APIs
    path("add/", add_turf),                                  # POST /turfs/add/
    path("<int:turf_id>/edit/", edit_turf),                  # PUT /turfs/5/edit/
    path("<int:turf_id>/upload-image/", upload_turf_image),  # POST /turfs/5/upload-image/
    path("image/<int:image_id>/delete/", delete_turf_image), # DELETE /turfs/image/10/delete/
]

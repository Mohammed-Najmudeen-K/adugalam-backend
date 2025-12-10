from rest_framework import serializers
from .models import Turf, TurfImage


class TurfImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TurfImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class TurfSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Turf
        fields = [
            "id",
            "name",
            "location",
            "price_per_hour",
            "description",
            "created_at",
            "images"
        ]

    def get_images(self, obj):
        images = TurfImage.objects.filter(turf=obj)
        return TurfImageSerializer(images, many=True, context=self.context).data

from django.shortcuts import get_object_or_404, render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from store.models import Category, Product
from .serializers import ProductSerilizer
from .filters import ProductFilter
from rest_framework.views import APIView
# Create your views here.

class CategoryListView(APIView):
    def get(self, request):
        categories = [
            {"value": key, "label": label}
            for key, label in Category.choices
        ]
        return Response(categories)

@api_view(["GET"])
def get_all_products(request):
    products = Product.objects.all()
    filterset = ProductFilter(request.GET,queryset=Product.objects.all().order_by('id'))
    serilizer = ProductSerilizer(filterset.qs,many=True)
    #print(filterset)
    return Response({"status":"success","categories":serilizer.data})

@api_view(["GET"])
def get_by_id_product(request,pk):
    product = get_object_or_404(Product,id=pk)
    serilizer = ProductSerilizer(product,many=False)
    print(product)
    return Response({"prodect":serilizer.data})




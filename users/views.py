"""User views"""
import pycountry as pycountry
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import mixins, viewsets
from rest_framework.generics import ListAPIView

from mitxpro.permissions import UserIsOwnerPermission
from users.models import User
from users.serializers import PublicUserSerializer, UserSerializer, CountrySerializer


class UserRetrieveViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """User retrieve viewsets"""

    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope, UserIsOwnerPermission]
    required_scopes = ["user"]


class CurrentUserRetrieveViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """User retrieve viewsets for the current user"""

    # NOTE: this is a separate viewset from UserRetrieveViewSet because of the differences in permission requirements
    serializer_class = UserSerializer
    permission_classes = []

    def get_object(self):
        """Returns the current request user"""
        # NOTE: this may be a logged in or anonymous user
        return self.request.user


class CountriesStatesView(ListAPIView):
    permission_classes = []
    serializer_class = CountrySerializer

    def get_queryset(self):
        """Get generator for countries/states list"""
        country_code = self.kwargs.get('country_code', None)
        if country_code:
            return sorted(list(pycountry.subdivisions.get(country_code=country_code)), key=lambda state: state.name)
        return sorted(list(pycountry.countries), key=lambda country: country.name)


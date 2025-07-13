from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from problems.views import ProblemSetterRequiredMixin

class CreatorPortalView(ProblemSetterRequiredMixin, View):
    """
    Main view for the creator portal with links to create problems and contests
    """
    def get(self, request):
        is_authorized = request.user.is_authorized
        return render(request, 'creator/portal.html', {
            'title': 'Creator Portal',
            'is_authorized': is_authorized
        })

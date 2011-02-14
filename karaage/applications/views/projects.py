# Copyright 2007-2010 VPAC
#
# This file is part of Karaage.
#
# Karaage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Karaage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Karaage  If not, see <http://www.gnu.org/licenses/>.

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import permission_required, login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

import datetime

from karaage.applications.models import ProjectApplication, Application
from karaage.applications.forms import ProjectApplicationForm, UserApplicantForm, ApproveProjectApplicationForm
from karaage.applications.emails import send_project_request_email
from karaage.machines.models import MachineCategory
from karaage.util import log_object as log


def do_projectapplication(request, token=None, application_form=ProjectApplicationForm, mc=MachineCategory.objects.get_default()):
    if request.user.is_authenticated():
        messages.info(request, "You are already logged in")
        return HttpResponseRedirect(reverse('kg_user_profile'))

    if token:
        application = get_object_or_404(ProjectApplication, secret_token=token)
        if application.state not in (Application.NEW, Application.OPEN):
            raise Http404
        applicant = application.applicant
        application.state = Application.OPEN
        application.save()
    else:
        if not settings.ALLOW_REGISTRATIONS:
            return render_to_response('applications/registrations_disabled.html', {}, context_instance=RequestContext(request)) 
        application = None
        applicant = None
    if request.method == 'POST':
        form = application_form(request.POST, instance=application)
        applicant_form = UserApplicantForm(request.POST, instance=applicant)
        if form.is_valid() and applicant_form.is_valid():
            applicant = applicant_form.save()
            application = form.save(commit=False)
            application.applicant = applicant
            application.save()
            application.submitted_date = datetime.datetime.now()
            application.state = Application.WAITING_FOR_DELEGATE
            application.save()
            application.machine_categories.add(mc)
            send_project_request_email(application)
            return HttpResponseRedirect(reverse('kg_application_done',  args=[application.secret_token]))
    else:
        form = application_form(instance=application)
        applicant_form = UserApplicantForm(instance=applicant)
    
    return render_to_response('applications/projectapplication_form.html', {'form': form, 'applicant_form': applicant_form, 'application': application}, context_instance=RequestContext(request)) 


@login_required
def approve_projectapplication(request, application_id):
    application = get_object_or_404(ProjectApplication, pk=application_id)
    if not request.user.get_profile() == application.institute.delegate:
        return HttpResponseForbidden('<h1>Access Denied</h1>')
    if application.state != Application.WAITING_FOR_DELEGATE:
        return render_to_response('applications/unable_to_approve.html', {'application': application }, context_instance=RequestContext(request))

    if request.method == 'POST':
        form = ApproveProjectApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save()
 
            application.approve()
            #send_project_approved_email(application)
            log(request.user, application, 2, 'Delegate approved')
            return HttpResponseRedirect(reverse('kg_userapplication_complete', args=[application.id]))
    else:
        form = ApproveProjectApplicationForm(instance=application)

    return render_to_response('applications/projectapplication_approve.html', {'form': form, 'application': application}, context_instance=RequestContext(request))

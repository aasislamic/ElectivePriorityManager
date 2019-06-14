from django.contrib import admin
# Create your views here.
from django.template.response import TemplateResponse

from apps.algorithm.generic_algorithm import GenericAlgorithm
from apps.authuser.models import StudentProxyModel
from apps.course.forms import StreamForm
from apps.course.models import ElectiveSubject
from apps.utils import check_if_the_data_entry_is_complete, \
    get_outliers_message, prepare_pandas_dataframe_from_database, get_normalized_result_from_dataframe


def get_admin_context():
    return {
        'site_title': admin.site.site_title,
        'site_header': admin.site.site_header,
        'site_url': admin.site.site_url,
    }


def display_report(request, *args, **kwargs):
    context = get_admin_context()
    context['has_data'] = False
    if request.method == 'GET':
        form = StreamForm
    else:
        form = StreamForm(request.POST)
        if form.is_valid():
            stream = form.cleaned_data.get('stream', None)
            semester = form.cleaned_data.get('semester', None)
            batch = form.cleaned_data.get('batch', None)
            subjects = ElectiveSubject.objects.filter(elective_for=semester, stream=stream).values_list('id',
                                                                                                        flat=True)
            student_queryset = StudentProxyModel.objects.filter(batch=batch, stream=stream)
            is_data_entry_complete = check_if_the_data_entry_is_complete(batch, stream, semester)
            context['has_data'] = True
            context['is_data_entry_ok'] = is_data_entry_complete
            if is_data_entry_complete:
                prepare_pandas_dataframe_from_database(batch, semester, stream)
                algo = GenericAlgorithm(batch, semester, stream)
                result_as_df = algo.run()
                normalized_result = get_normalized_result_from_dataframe(result_as_df)
                # AlgorithClass = get_suitable_algorithm_class(semester.subjects_provided)
                # algorithm = AlgorithClass(student_queryset, semester, list(subjects))
                # algorithm.run()
                # normalized_result = normalize_result(algorithm.get_result())
                context['result'] = normalized_result
            else:
                outlier_messages = get_outliers_message(batch, stream, semester)
                context['outlier_messages'] = outlier_messages
                context['available_subject_count'] = len(subjects)
            context['is_download'] = '_get_pdf' in request.POST
    context['form'] = form
    return TemplateResponse(
        request,
        'admin/course/display_report.html',
        context
    )

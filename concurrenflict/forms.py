import simplejson
from django import forms
from django.core import serializers
from django.utils.html import mark_safe


class ConcurrenflictFormMixin(forms.ModelForm):
    """
    Compares model instance between requests: first at for render, then upon submit but before save (i.e. on clean).
    If model instances are different, the Form fails validation and displays what has been changed.
    """

    concurrenflict_initial = forms.CharField(widget=forms.HiddenInput, label="", required=False)
    _concurrenflict_json_data = ''
    concurrenflict_field_name = 'concurrenflict_initial'

    def _get_concurrenflict_field(self):
        return self.fields[self.concurrenflict_field_name]

    def __init__(self, *args, **kwargs):
        super(ConcurrenflictFormMixin, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            self._concurrenflict_json_data = serializers.serialize('json', [instance])
            self._get_concurrenflict_field().initial = self._concurrenflict_json_data

    def clean(self):
        self.cleaned_data = super(ConcurrenflictFormMixin, self).clean()
        json_at_get = self.cleaned_data[self.concurrenflict_field_name]
        del self.cleaned_data[self.concurrenflict_field_name]
        json_at_post = self._concurrenflict_json_data
        # we want to keep using the initial data set in __init__()
        self.data = self.data.copy()
        self.data[self.concurrenflict_field_name] = self._concurrenflict_json_data
        have_diff = False

        # if json_at_post is None then this is an add() rather than a change(), so
        # there's no old record that could have changed while this one was being worked on
        if json_at_post and json_at_get and (json_at_post != json_at_get):

            json_data_before = simplejson.loads(json_at_get)
            json_data_after = simplejson.loads(json_at_post)

            serial_data_before = serializers.deserialize('json', json_at_get).next()
            model_before = serial_data_before.object
            m2m_before = serial_data_before.m2m_data
            serial_data_after = serializers.deserialize('json', json_at_post).next()
            model_after = serial_data_after.object
            m2m_after = serial_data_after.m2m_data

            fake_form = self.__class__(instance=model_after, prefix='concurrenflict')

            for field in model_before._meta.fields + m2m_before.keys():
                try:
                    key = field.name
                except AttributeError:
                    key = field  # m2m_before is dict, model._meta.fields is list of Fields
                if key == self.concurrenflict_field_name:
                    continue
                if key not in fake_form.fields.keys():
                    continue
                json_value_before = json_data_before[0]['fields'].get(key, None)
                json_value_after = json_data_after[0]['fields'].get(key, None)
                if json_value_after != json_value_before:
                    value_before = getattr(model_before, key, m2m_before.get(key))
                    value_after = getattr(model_after, key, m2m_after.get(key, ''))
                    have_diff = True
                    fake_form.data[key] = value_after
                    # this does not work for MultiSelect widget (and other Multi-something) widgets:
                    # ANDDD this appears to not be thread-safe! (faceplam)
                    #fake_form[key].field.widget.attrs['disabled'] = 'disabled'
                    # so to make sure:
                    js_fix = '''
                    <script type="text/javascript">
                        (function($){
                            $(function(){
                                $('[name^="%(html_name)s"]').attr('disabled', 'disabled').attr('readonly', 'readonly');
                                $('#add_id_%(html_name)s').remove();
                            });
                        })(window.jQuery || django.jQuery);
                    </script>
                    ''' % {'html_name': fake_form[key].html_name}

                    temp_field = unicode(fake_form[key])
                    msg = mark_safe(u'This field has changed! New Value: <div class="concurrenflict_disabled_widget">%s</div>%s'
                                    % (temp_field, js_fix,))
                    #@TODO Django 1.7: use Form.add_error()
                    self._errors[key] = self.error_class([msg])

                    # These fields are no longer valid. Remove them from the
                    # cleaned data. As if that has any effect...
                    del self.cleaned_data[key]

        if have_diff:
            raise forms.ValidationError(u"This record has changed since you started editing it.")

        return self.cleaned_data


class ModelForm(ConcurrenflictFormMixin, forms.ModelForm):
    pass

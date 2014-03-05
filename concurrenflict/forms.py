import simplejson
from django import forms
from django.core import serializers
from django.utils.html import mark_safe, escape

class ConcurrenflictFormMixin(forms.ModelForm):

    # TODO: make it hide the colon before our empty label - move the whole thing to .as_p() et al.
    concurrenflict_initial = forms.CharField(
        widget=forms.HiddenInput,
        label="",
        required=False)

    _concurrenflict_json_data = ''

    concurrenflict_field_name = 'concurrenflict_initial'

    def _get_concurrenflict_field(self):
        return self.fields[self.concurrenflict_field_name]

    def __init__(self, *args, **kwargs):
        super(ConcurrenflictFormMixin, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            opts = self._meta
            object_data = forms.model_to_dict(instance, opts.fields, opts.exclude)
            #self._concurrenflict_json_data = serializers.serialize('json',  [instance], fields=object_data.keys())
            self._concurrenflict_json_data = simplejson.dumps(object_data)
            self._get_concurrenflict_field().initial = self._concurrenflict_json_data


    def clean(self):
        #@TODO revize and make a docstring

        # The 'model_json' field is hidden, and as such the user can't change it
        # (at least without hacking on the POST data).
        # So the value we get back for the 'model_json' field is effectively the value
        # it was set to by a previous instance of this form's __init(), when the form
        # was created to send the data to the user on the GET.
        #
        # Our instance was instantiated on the POST, and so we too will have set model_json's
        # initial value based on the state of the model at the time of the POST.
        #
        # So the apparent new value is the value from the original GET and the apparent
        # old value, the 'initial' value is the value from the time of the POST.
        #
        # Normally those will be the same, since we've not yet saved any changes the user
        # has made (we're about to validate those changes now...). However, if someone
        # else changed the model in the meantime, then those two values will no longer match,
        # and that's what we're trying to catch.


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
        if json_at_post and (json_at_post != json_at_get):

            data_at_get = simplejson.loads(json_at_get)
            data_at_post = simplejson.loads(json_at_post)

            temp_form = self.__class__(initial=data_at_post, prefix='concurenflict')

            for key, val_at_get in data_at_get.iteritems():
                if key == self.concurrenflict_field_name:
                    continue
                #if isinstance(val_at_get, basestring):
                #    val_at_get = unicode(val_at_get)
                val_at_post = data_at_post.get(key, '')
                #if isinstance(val_at_post, basestring):
                #    val_at_post = unicode(val_at_get)
                if val_at_post != val_at_get:

                    have_diff = True

                    # this does not render on MultySelect widget (and other Multy-something, it seems)
                    # temp_form[key].field.widget.attrs['disabled'] = 'disabled'

                    js_fix = '''
                    <script type="text/javascript">
                        (function($){
                            $(function(){
                                $('[name^="%(html_name)s"]').attr('disabled', 'disabled');
                                $('#add_id_%(html_name)s').remove();
                            });
                        })(window.jQuery||django.jQuery);
                    </script>
                    ''' % {'html_name': temp_form[key].html_name}

                    temp_form.data[key] = val_at_post

                    temp_field = unicode(temp_form[key])

                    msg = mark_safe(u'This field has changed! New Value: <div>%s</div>%s' % (temp_field, js_fix,) )

                    #@TODO Django 1.7 use Form.add_error()
                    # We know these are not in self._errors now
                    self._errors[key] = self.error_class([msg])

                    # These fields are no longer valid. Remove them from the
                    # cleaned data.
                    # del self.cleaned_data[key]

        if have_diff:
            raise forms.ValidationError(u"This record has changed since you started editing it.")

        return self.cleaned_data


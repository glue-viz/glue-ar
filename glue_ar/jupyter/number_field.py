import traitlets
import ipyvuetify as v


# Based on https://github.com/widgetti/ipyvuetify/issues/241
class NumberField(v.VuetifyTemplate):
    label = traitlets.Unicode().tag(sync=True)
    value = traitlets.Unicode().tag(sync=True)

    temp_error = traitlets.Unicode(allow_none=True, default_value=None).tag(sync=True)

    def __init__(self, type, label, error_message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number_type = type
        self.label = label
        self.error_message = error_message

    @traitlets.default("template")
    def _template(self):
        return """
            <v-text-field
              :label="label"
              type="number"
              v-model="value"
              @change="temp_rule"
              :rules="[temp_error]"
            >
            </v-text-field>
        """

    def vue_temp_rule(self, value):
        self.temp_error = None
        try:
            self.number_type(value)
        except ValueError:
            self.temp_error = self.error_message

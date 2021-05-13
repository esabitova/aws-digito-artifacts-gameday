import datetime
import re


class InputValidator:
    """
    Validator that checks that the input string matches the specific format
    """
    @staticmethod
    def validate_small_case_numeric_with_hyphens(input_text: str):
        """
        Validates the string contains only small case alphabets, numbers and hyphens
        :param input_text: input text
        :return: input text
        """
        return InputValidator.validate_input(input_text, "^[a-z]{1}[a-z0-9\\-]+$")

    @staticmethod
    def validate_small_case_with_underscore(input_text: str):
        """
        Validates the string contains only small case alphabets and underscores
        :param input_text: input text
        :return: input text
        """
        return InputValidator.validate_input(input_text, "[a-z_]+")

    @staticmethod
    def validate_alpha(input_text: str):
        """
        Validates the string contains only small case alphabets
        :param input_text: input text
        :return: input text
        """
        return InputValidator.validate_input(input_text, "[A-Za-z]+")

    @staticmethod
    def validate_boolean_inputs(input_text: str):
        """
        Validates the string is either yes or no
        :param input_text: input text
        :return: input text
        """
        return InputValidator.validate_input(input_text, "yes|no")

    @staticmethod
    def validate_alpha_numeric_input(input_text: str):
        return InputValidator.validate_input(input_text, "[a-zA-Z0-9]+")

    @staticmethod
    def validate_date_input(input_text: str):
        """
        Validates the input date is valid
        :param input_text: input text
        :return: input text
        """
        try:
            datetime.datetime.strptime(input_text, '%Y-%m-%d')
            return input_text
        except ValueError:
            raise ValueError("Input date {} did not match the expected format YYYY-MM-DD".format(input_text))

    @staticmethod
    def validate_one_of(input_text: str, allowed_values: list):
        """
        Validates that input text is one of the specified allowed values
        :param input_text: input text
        :param allowed_values: list of allowed values
        :return: input text
        """
        if input_text not in allowed_values:
            raise ValueError("Input {} did not match one of {}".format(input_text, allowed_values))
        return input_text

    @staticmethod
    def validate_one_or_more_of(input_text: str, allowed_values: list):
        """
        Validates that the comma separated input string only contains values from the allowed list
        :param input_text: comma separated input string
        :param allowed_values:  list of allowed values
        :return: input text
        """
        input_values = [input_text]
        if "," in input_text:
            input_values = input_text.split(",")
        for value in input_values:
            if value not in allowed_values:
                raise ValueError("Input {} should be one of more of {}".format(input_text, allowed_values))
        return ",".join(set(input_values))

    @staticmethod
    def validate_input(input_text: str, regex: str):
        """
        Validate that the input string matches the specified regular expression pattern
        :param input_text: input text
        :param regex: expected regular expression pattern
        :return: input text
        """
        if re.fullmatch(regex, input_text) is None:
            raise ValueError("Input {} did not match {}".format(input_text, regex))
        return input_text

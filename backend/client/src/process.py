from typing import Any
from .configs import logger
import json
import operator

class ProcessData:
    """
    ProcessData class for validating and processing alert data based on predefined rules.
    This class provides a generic framework for monitoring various entities (power plant,
    hospital) against configurable validation rules. It checks values against thresholds using
    custom operators and generates alert messages when violations are detected.

    Attributes:
        USINA_RULES (list): Validation rules for power plant monitoring, checking parameters like
            purity, pressure, and dew point against defined thresholds.
        FLAG_RULES (list): Validation rules for fault flag detection, checking for critical
            failure states like RST failure and emergency button activation.
        HOSPITAL_RULES (list): Validation rules for hospital monitoring, checking pressure
            and dew point parameters.

    Methods:
        check_rules(values, rules, safe_get): Execute validation rules generically against
            a values dictionary and return formatted error messages for failed rules.
        process_alert(name, hospital, values, rules, safe_get, extra_data): Process alerts
            based on rule validation and generate alert title and body with fault details.
        _handle_usina_email(data): Process power plant alert data by extracting and
            merging PSA and central values, then generating alert email content.
        _handle_hospital_email(data): Process hospital alert data and generate alert email
            content based on hospital-specific validation rules.

    Private Methods:
        __safe_get(value, default): Safely convert values to float with fallback to default
            if conversion fails or value is None.
    """

    USINA_RULES = [
        ("purity",            operator.lt,  90.0,  "Low purity: {value}%"),
        ("product_pressure",  operator.lt,   5.0,  "Low product pressure: {value}"),
        ("pressure",          operator.lt,   5.0,  "Low central pressure: {value}"),
        ("dew_point",         operator.gt, -45.0,  "High dew point: {value}"),
        ("rede",              operator.lt,   5.0,  "Low network pressure: {value}"),
    ]

    FLAG_RULES = [
        ("RST", operator.ne, "OK", "RST failure detected"),
        ("BE",  operator.ne, "OK", "Emergency button activated"),
    ]

    HOSPITAL_RULES = [
        ("pressure", operator.lt, 5.0, "Low pressure: {value}"),
        ("rede",     operator.lt, 5.0, "Low network pressure: {value}"),
        ("dew_point", operator.gt, -45.0, "High dew point: {value}"),
    ]

    @staticmethod
    def check_rules(values: dict, rules: list, safe_get) -> list[str]:
        """
        Execute validation rules generically against a values dictionary.
        Args:
            values (dict): Dictionary containing the values to be validated.
            rules (list): List of tuples containing (key, operator, limit, message) where:
                - key (str): Dictionary key to retrieve the value from.
                - op (callable): Binary operator function that compares value and limit.
                - limit: Threshold or reference value for comparison.
                - message (str): Format string for the result message, supports {value} placeholder.
            safe_get (callable): Function to safely retrieve and normalize the value.
        Returns:
            list[str]: List of formatted error/warning messages for rules that evaluated to True.
        """
        results = []
        for key, op, limit, message in rules:
            value = safe_get(values.get(key), limit)
            if op(value, limit):
                results.append(message.format(value=value))
        return results

    @classmethod
    def process_alert(cls, name: str,
        hospital: str, values: dict,
        rules: list, safe_get,
        extra_data: dict | None = None
    ):
        """
        Process alerts based on rule validation against provided values.
        Checks both custom rules and predefined flag rules against the provided values.
        If any faults are detected, generates an alert message with details.
        Args:
            cls: Class reference for method calls.
            name (str): The name of the entity being monitored.
            hospital (str): The hospital identifier associated with the alert.
            values (dict): Dictionary of values to be validated against rules.
            rules (list): List of custom rules to validate against values.
            safe_get: Function to safely retrieve values from the values dictionary.
            extra_data (dict | None, optional): Additional data to include in alert body.
                Defaults to None.
        Returns:
            tuple: A tuple containing:
                - str: Alert title or status message.
                - str: Alert body with details or hospital identifier.
                If faults detected: ("ALERT {name} {hospital}", alert_body)
                If no faults: ("No issues detected", hospital)
        """
        faults = cls.check_rules(values, rules, safe_get) + \
                cls.check_rules(values, cls.FLAG_RULES, safe_get)

        if faults:
            logger.info(f"Issues detected in {name} {hospital}: {faults}")

            body = (
                f'ALERT: Issues detected in {name} {hospital}\n\n'
                f'Identified issues:\n' +
                '\n'.join(f'- {f}' for f in faults)
            )

            if extra_data:
                body += (
                    f'\n\nFull data:\n'
                    f'{json.dumps(extra_data, indent=2, ensure_ascii=False)}'
                )

            return f'ALERT {name} {hospital}', body

        return "No issues detected", hospital

    @staticmethod
    def __safe_get(value: Any, default: Any) -> Any:
        """
        Safely retrieve a numeric value with a fallback default.

        Converts the input value to a float and returns it if the conversion is successful.
        If the value is None or cannot be converted to a numeric type, returns the provided default value.

        Args:
            value (Any): The value to be converted to float.
            default (Any): The default value to return if value is None or not numeric.

        Returns:
            Any: The value converted to float, or the default value if conversion fails or value is None.

        Examples:
            >>> __safe_get(42, 0)
            42.0
            >>> __safe_get("3.14", 0)
            3.14
            >>> __safe_get(None, 0)
            0
            >>> __safe_get("invalid", 0)
            0
        """
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def _handle_usina_email(cls, data):
        """
        Process power plant alert email data by extracting PSA and central values.
        This method retrieves power plant and central data from the input, merges them,
        and processes an alert using predefined power plant rules to generate an email
        subject and body.
        Args:
            cls: Class reference for accessing class methods and constants.
            data (dict): Input data dictionary containing:
                - "Data" (dict): Dictionary with "usina" and "central" keys.
                - "Hospital" (str): Hospital identifier for the alert.
        Returns:
            tuple: A tuple containing:
                - subject (str): Email subject line.
                - body (str): Email body content.
        Example:
            >>> data = {
            ...     "Data": {"usina": {"param1": 100}, "central": {"param2": 50}},
            ...     "Hospital": "Hospital ABC"
            ... }
            >>> subject, body = cls._handle_usina_email(data)
        """
        psa = data["Data"]
        all_values = {**psa}
       
        subject, body = cls.process_alert(
            name="Oxygen Plant",
            hospital=data["Hospital"],
            values=all_values,
            rules=cls.USINA_RULES,
            safe_get=cls.__safe_get,
            extra_data={"psa": psa}
        )
        return subject, body

    @classmethod
    def _handle_hospital_email(cls, data):
        """
        Process hospital email data and generate an alert based on predefined rules.
        Args:
            cls: The class instance.
            data (dict): A dictionary containing hospital email data with keys:
                - "Data" (dict): Hospital data to be processed.
                - "Hospital" (str): The hospital identifier or name.
        Returns:
            The result of process_alert() method with hospital-specific rules and data.
        Raises:
            KeyError: If required keys ("Data" or "Hospital") are missing from the input data.
        """
        hospital = data["Data"]
        return cls.process_alert(
            name="Hospital",
            hospital=data["Hospital"],
            values=hospital,
            rules=cls.HOSPITAL_RULES,
            safe_get=cls.__safe_get,
            extra_data=hospital
        )

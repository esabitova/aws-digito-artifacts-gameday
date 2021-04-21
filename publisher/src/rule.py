class Rule:
    def __init__(self, required_document_elements, required_parameters, required_outputs, required_steps):
        self.required_document_elements = required_document_elements
        self.required_parameters = required_parameters
        self.required_outputs = required_outputs
        self.required_steps = required_steps

class MessageTemplate:
    def __init__(self, template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            self.template = f.read()

    def render(self, annonce):
        # Exemple simple d'injection
        return self.template.format(**annonce)

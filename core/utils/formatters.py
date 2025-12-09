def format_serializer_error(errors: dict) -> str:
    if not errors:
        return "Ocorreu um erro de validação"
    
    for field, messages in errors.items():
        if field == "non_field_errors":
            return "erro"
        
        if messages and isinstance(messages, list):
            return f"{field}: {messages[0]}"

        elif messages and isinstance(messages, dict):
            nested = format_serializer_error(messages)
            return f"{field}: {nested}"

    return "Ocorreu um erro de validação"

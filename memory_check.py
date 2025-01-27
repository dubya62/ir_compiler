def is_variable(token):
    return len(token) > 0 and token[0] == "#"


def is_string_literal(token):
    return len(token) > 0 and token[0] == '"'


def is_char_literal(token):
    return len(token) > 0 and token[0] == "'"


def is_int_literal(token):
    try:
        result = str(int(token))
        return result == token
    except:
        pass
    return False


def is_float_literal(token):
    try:
        float(token)
        return True
    except:
        pass
    return False


def is_literal(token):
    return is_string_literal(token) or is_char_literal(token) or is_int_literal(token) or is_float_literal(token)

#test = "Hello, World!"


# array access index
    # index cannot be outside of the array
# leftval / rightval
    # rightval cannot be 0
# leftval % rightval
    # rightval cannot be 0


def check_memory(tokens: list[str]):
    
    def is_signed(variable): 
        type_string = TEST_TYPES.get(variable, "")
        return type_string.startswith("i")
    
    def check_signed_overflow(left, right, operation): 
        INT32_MIN, INT32_MAX = -2**31, 2**31 - 1
        
        if operation == "+":
            if left > 0 and right > 0 and left > INT32_MAX - right:
                raise ValueError(f"Overflow detected in addition: {left} + {right} exceed over the limit of {INT32_MAX}.")
            elif left < 0 and right < 0 and left < INT32_MIN - right: 
                raise ValueError(f"Overflow detected in addition: {left} + {right} exceed below the limit of {INT32_MIN}.")
        
        elif operation == "-": 
            if left > 0 and right < 0 and left > INT32_MAX + right: 
                raise ValueError(f"Overflow detected in subtraction: {left} - ({right}) exceed over the limit of {INT32_MAX}.")
            elif left < 0 and right > 0 and left < INT32_MIN + right: 
               raise ValueError (f"Overflow detected in subtraction: {left} - ({right}) exceed below the limit of {INT32_MIN}.")
           
        elif operation == "*": 
            if left != 0 and right != 0 : 
                if left > 0 and right > 0 and left > INT32_MAX // right: 
                    raise ValueError(f"Overflow detected in multiplication: {left} * {right} exceed over the limit of {INT32_MAX}.")
                elif left < 0 and right < 0 and left < INT32_MAX // right: 
                    raise ValueError(f"Overflow detected in multiplication: {left} * {right} exceed below the limit of {INT32_MAX}.")
                elif left < 0 or right < 0:
                    if left == INT32_MIN or right == INT32_MIN: 
                        raise ValueError(f"Overflow detected in multiplication: {left} * {right} exceed below the limit of {INT32_MIN}")
                    if abs(left) > abs(INT32_MAX // right): 
                        raise ValueError(f"Overflow detected in multiplication: {left} * {right} exceed below the limit of {INT32_MIN}")
                    
        elif operation == "/": 
            if right == 0: 
                raise ValueError("Cannot divide by zero.")
            if left == INT32_MIN and right == -1: 
                raise ValueError(f"Overflow detected in division: {left} / {right} exceed over the limit of {INT32_MAX}.")
            
        elif operation == "<<": 
            if right < 0 or right >= 32: 
                raise ValueError(f"Invalid shift count: {right}. Must be between 0 and 31.")
            if left > INT32_MAX >> right:
                raise ValueError(f"Overflow detected in left shift: {left} << {right} exceeds the limit of {INT32_MAX}.")
            
        elif operation == ">>": 
            if right < 0 or right >= 32: 
                raise ValueError(f"Invalid shift count: {right}. Must be between 0 and 31.")
                    

    # Keep track of which variables can have which values
    POSSIBLE_VALUES = {}
    ALLOCATED_MEMORY = {}

    i = 0
    n = len(tokens)
    # Iterate through list
    while i < n:
        token = tokens[i]
        # If it's a variable
        if is_variable(tokens[i]):
            # If this variable is being assigned a value, update its possible values
            if i + 1 < n and tokens[i + 1] == "=":
                assigned_value = tokens[i + 2]  # Value after the "=" sign
                if is_literal(assigned_value):
                    if tokens[i] not in POSSIBLE_VALUES:
                        POSSIBLE_VALUES[tokens[i]] = set()
                    POSSIBLE_VALUES[tokens[i]].add(assigned_value)

        elif tokens[i] == "access":
            # Make sure the token (array) before this token is large enough to be indexed
            array_name = tokens[i - 1]
            index = tokens[i + 1]
            if is_variable(index):
                if array_name in POSSIBLE_VALUES:
                    if index not in POSSIBLE_VALUES[array_name]:
                        print(f"Warning: You're trying to access an index out of bounds for array {array_name}.")

        elif tokens[i] in ["%", "/"]:
            # Ensure the token after this token cannot be 0
            right_operand = tokens[i + 1]
            if right_operand == "0":
                if tokens[i] == "%":
                    raise ValueError("Error: Modulo by zero is not allowed!")
                elif tokens[i] == "/":
                    raise ValueError("Error: Division by zero detected!")

        i += 1
        


def test_check_memory(): 
    test_tokens = [
        "#7", "=", "#1", "<", "2", ";", 
        "if", "(", "#7", ")", "{", 
            "#10", "=", '"HELLO, WORLD!\n"', ";", 
            "#3", "call", "#10", ";", 
            "#11", "=", "10", "*", "3", ";", 
            "#12", "=", "#11", "-", "2", ";", 
            "#8", "=", "#12", ";", 
            "#13", "access", "0", "=", "#8", ";", 
            "return", ";"
        "}", "else", "{", "}", 
        "#4", "=", "2", ";", 
        "#5", "=", "3", ";", 
        "#6", "=", "#4", "<<", "#5", ";", 
        "#9", "=", "#6", ";", 
        "#13", "access", "0" "=", "#9", ";"
        "return", ";"
    ]
    
    try: 
        check_memory(test_tokens)
        print("Test with test_tokens passed. No division or modulo by zero detected.")
    except ValueError as e: 
        print(f"Test with test_tokens failed: {e}")
    except Exception as e: 
        print(f"Test with test_tokens failed with unexpected error: {e}")
    
    
def test_check_memory_invalid_tokens():
    invalid_tokens_cases = [
        (["#1", "/", "0", ";"], "Error: Division by zero detected!"),
        (["#1", "%", "0", ";"], "Error: Modulo by zero is not allowed!"),
    ]
    
    for i, (tokens, expected_message) in enumerate(invalid_tokens_cases):
        try:
            check_memory(tokens)
            print(f"Test case {i+1} failed: Expected '{expected_message}' but got no warning or error.")
        except ValueError as e:
            if str(e) == expected_message:
                print(f"Test case {i+1} passed.")
            else:
                print(f"Test case {i+1} failed: Expected '{expected_message}' but got '{e}'.")
        except Exception as e:
            print(f"Test case {i+1} failed with unexpected exception: {e}")


if __name__ == "__main__":
    print()
    test_check_memory()
    print("\nInvalid tokens test cases:\n")
    test_check_memory_invalid_tokens()
 

"""
User-friendly entry point for examples.

Usage: ./mcu build examples
"""

import examples  # FIXME: how to import all examples without hard coding their module name ?
print(examples)

print("""

    Welcome to the examples and congrats for installing ITIOT !

    You can view a list of all examples by typing:

        examples

    You can load an examples by typing:

        import example_name

    For example, load the example 'tutorial' by typing:

        import tutorial

- Enjoy !

""")

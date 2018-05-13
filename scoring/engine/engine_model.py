from data_model import *
import json

class EngineModel(DataModel):

    def load_check_ios(self, credentials):
        """ 
        Load check input-output pairs from the database.

        Arguments:
            credentials (List(Credential)): List of credentials to associate
            input-output pairs with

        Returns:
            Dict(int->List(CheckIO)): Mapping of check IDs to a list of
                check input-output pairs
        """
        check_ios = super().load_check_ios(credentials)
        for check_id,cios in check_ios.items():
            for cio in cios:
                poll_input = cio.poll_input
                input_class_str, input_args = json.loads(poll_input)
                input_class = load_module(input_class_str)
                poll_input = input_class(**input_args)
                cio.poll_input = poll_input
        return check_ios

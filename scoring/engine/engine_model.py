from data_model import *
import json

class EngineModel(DataModel):

    def load_check_ios(self, credentials):
        """ 
        Load check input-output pairs from the database.

        Arguments:
            credentials (List(Credential)): List of credentials to associate input-output pairs with

        Returns:
            Dict(int->List(CheckIO)): Mapping of check IDs to a list of check input-output pairs
        """
        check_ios = super().load_check_ios(credentials)
        for check_id,cios in check_ios.items():
            for cio in cios:
                poll_input = cio.poll_input
                input_class_str, input_args = json.loads(poll_input)
                input_class = load_module(input_class_str)

                if 'team' in input_args:
                    id = input_args['team']
                    input_args['team'] = [t for t in self.teams if t.id == id][0]
                if 'credentials' in input_args:
                    id = input_args['credentials']
                    input_args['credentials'] = [c for c in self.credentials if c.id == id][0]

                poll_input = input_class(**input_args)
                cio.poll_input = poll_input
        return check_ios

from model import Model
from utils import load_module
import json

class EngineModel(Model):

    def load_check_ios(self, credentials):
        """ 
        Load CheckIOs from the database.

        Arguments:
            credentials (List(Credential)): List of credentials to associate CheckIOs with

        Returns:
            Dict(int->List(CheckIO)): Mapping of check IDs to a list of CheckIOs
        """
        check_ios = super().load_check_ios(credentials)
        for check_id,cios in check_ios.items():
            for cio in cios:
                # Rebuild the PollInput
                poll_input = cio.poll_input
                input_class_str, input_args = json.loads(poll_input)
                input_class = load_module(input_class_str)
                poll_input = input_class.deserialize(input_class, input_args, self.teams, self.credentials)

                cio.poll_input = poll_input
        return check_ios

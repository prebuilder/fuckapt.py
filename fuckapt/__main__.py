from plumbum import cli

from . import triggers


class CLI(cli.Application):
	pass


@CLI.subcommand("trigger")
class TriggerCLI(cli.Application):
	def main(self):
		pass


if __name__ == "__main__":
	CLI.run()

import sys

from litedram.generate import generate

def main():
    # get config
    if len(sys.argv) < 2:
        print("missing config file")
        exit(1)
    exec(open(sys.argv[1]).read(), globals())

    #Try to execute the config file as Python code first
    if 'core_config' in globals():
        core_config = globals()['core_config']
    # Failed to read config as Python. Try yaml instead
    else:
        import yaml
        core_config = yaml.safe_load(open(sys.argv[1]))['core_config']

    generate(core_config)

if __name__ == "__main__":
    main()


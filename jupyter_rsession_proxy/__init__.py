import os
import tempfile
import subprocess
import getpass
import shutil
from textwrap import dedent

# TODO: consider writing launcher scripts on demand
#       or some other way, that makes conda env configurable somehow

def setup_shiny():
    '''Manage a Shiny instance.'''

    def _get_shiny_cmd(port):
        # server.r_path ???
        conf = dedent("""
            run_as {user};
            server {{
                bookmark_state_dir {site_dir}/shiny-server-boomarks;
                listen {port};
                location / {{
                    site_dir {site_dir};
                    log_dir {site_dir}/logs;
                    directory_index on;
                }}
            }}
        """).format(
            user=getpass.getuser(),
            port=str(port),
            site_dir=os.getcwd()
        )

        f = tempfile.NamedTemporaryFile(mode='w', delete=False)
        f.write(conf)
        f.close()
        return ['shiny-server-launcher', f.name]

    def _get_shiny_env(port):
        env = get_r_env()
        return env

    return {
        'command': _get_shiny_cmd,
        'launcher_entry': {
            'title': 'Shiny',
            'icon_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'shiny.svg')
        }
    }


def setup_rstudio():

    def _get_rsession_env(port):
        env = {}

        # rserver needs USER to be set to something sensible,
        # otherwise it'll throw up an authentication page
        if not os.environ.get('USER', ''):
            env['USER'] = getpass.getuser()

        return env

    def _get_r_executable():
        try:
            # get notebook app
            from notebook.notebookapp import NotebookApp
            nbapp = NotebookApp.instance()
            # get R executable:
            kernel_name = nbapp.kernel_manager.default_kernel_name
            if kernel_name:
                kernel_spec = nbapp.kernel_spec_manager.get_kernel_spec(kernel_name)
                # nb_conda_kernels has conda env prefix at idx 4
                return '{}/bin/R'.format(kernel_spec.argv[4])
        except Exception:
            nbapp.log.warning('Error when trying to get R executable from kernel')
        return 'R'

    def _get_rsession_cmd(port):
        # Other paths rsession maybe in
        other_paths = [
            # When rstudio-server deb is installed
            '/usr/lib/rstudio-server/bin/rserver',
        ]
        if shutil.which('rserver'):
            executable = 'rserver'
        else:
            for op in other_paths:
                if os.path.exists(op):
                    executable = op
                    break
            else:
                raise FileNotFoundError('Can not find rserver in PATH')

        cmd = [
            executable,
            '--www-port=' + str(port),
            '--rsession-which-r=' + _get_r_executable(),
            '--rsession-path=/usr/local/bin/rsession-launcher'
        ]
        return cmd

    return {
        'command': _get_rsession_cmd,
        'environment': _get_rsession_env,
        'launcher_entry': {
            'title': 'RStudio',
            'icon_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'rstudio.svg')
        }
    }

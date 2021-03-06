"""Common tasks for Invoke."""

import codecs
import os
import typing
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path
from tempfile import mkstemp

from blake2signer.utils import b64decode
from invoke import Context
from invoke import Exit
from invoke import Result
from invoke import task


@task
def flake8(ctx):
    """Run flake8 with proper exclusions."""
    ctx.run('flake8 --exclude tests asgi_signing_middleware/', echo=True)
    ctx.run('flake8 --ignore=S101,R701,C901 asgi_signing_middleware/tests/', echo=True)
    ctx.run('flake8 --ignore=S101,R701,C901 tests/', echo=True)
    ctx.run('flake8 tasks.py', echo=True)


@task
def pydocstyle(ctx):
    """Run pydocstyle with proper exclusions."""
    ctx.run('pydocstyle --explain asgi_signing_middleware/', echo=True)
    ctx.run('pydocstyle --explain tests/', echo=True)
    ctx.run('pydocstyle --explain tasks.py', echo=True)


@task
def darglint(ctx):
    """Run darglint."""
    ctx.run('darglint -v2 asgi_signing_middleware/', echo=True)
    ctx.run('darglint -v2 tests/', echo=True)
    ctx.run('darglint -v2 tasks.py', echo=True)


@task
def pylint(ctx):
    """Run pylint."""
    ctx.run('pylint asgi_signing_middleware/ --ignore tests', echo=True, pty=True, warn=True)
    ctx.run('pylint asgi_signing_middleware/tests/ --exit-zero', echo=True, pty=True, warn=True)
    ctx.run('pylint tests/ --exit-zero', echo=True, pty=True, warn=True)
    ctx.run('pylint tasks.py --exit-zero', echo=True, pty=True, warn=True)


@task
def bandit(ctx):
    """Run bandit with proper exclusions."""
    ctx.run('bandit -i -r -x asgi_signing_middleware/tests asgi_signing_middleware/', echo=True)
    ctx.run('bandit -i -r -s B101 asgi_signing_middleware/tests/', echo=True)
    ctx.run('bandit -i -r -s B101 tests/', echo=True)
    ctx.run('bandit -i -r tasks.py', echo=True)


@task
def mypy(ctx):
    """Lint code with mypy."""
    ctx.run('mypy asgi_signing_middleware/', echo=True, pty=True)
    ctx.run('mypy tests/', echo=True, pty=True)


@task
def yapf(ctx, diff=False):
    """Run yapf to format the code."""
    cmd = ['yapf', '--recursive', '--verbose', '--parallel']
    if diff:
        cmd.append('-d')
    else:
        cmd.append('-i')

    cmd.append('asgi_signing_middleware/')
    cmd.append('tests/')
    cmd.append('tasks.py')

    ctx.run(' '.join(cmd), echo=True)


@task
def trailing_commas(ctx):
    """Add missing trailing commas, or remove them if necessary."""
    opts = r'-type f -name "*.py" -exec add-trailing-comma "{}" \+'  # noqa: P103
    ctx.run('find asgi_signing_middleware/ ' + opts, echo=True, pty=True, warn=True)
    ctx.run('find tests/ ' + opts, echo=True, pty=True, warn=True)
    ctx.run('add-trailing-comma tasks.py', echo=True, pty=True, warn=True)


# noinspection PyUnusedLocal
@task(yapf, trailing_commas)
def reformat(ctx):  # pylint: disable=W0613
    """Reformat code (runs YAPF and add-trailing-comma)."""


# noinspection PyUnusedLocal
@task(flake8, pylint, pydocstyle, darglint, mypy, bandit)
def lint(ctx):  # pylint: disable=W0613
    """Lint code, and run static analysis.

    Runs flake8, pylint, pydocstyle, darglint, mypy, and bandit.
    """


@task
def clean(ctx):
    """Remove all temporary and compiled files."""
    remove = (
        'build',
        'dist',
        '*.egg-info',
        '.coverage',
        'cover',
        'htmlcov',
        '.mypy_cache',
        '.pytest_cache',
        'site',
    )
    ctx.run(f'rm -vrf {" ".join(remove)}', echo=True)
    ctx.run(r'find . -type d -name "__pycache__" -exec rm -rf "{}" \+', echo=True)  # noqa: P103
    ctx.run('find . -type f -name "*.pyc" -delete', echo=True)


@task(
    aliases=['test'],
    help={
        'watch': 'run tests continuously with pytest-watch',
        'seed': 'seed number to repeat a randomization sequence',
        'coverage': 'run with coverage (or not)',
    },
)
def tests(ctx, watch=False, seed=0, coverage=True):
    """Run tests."""
    if watch:
        cmd = ['pytest-watch', '--']
    else:
        cmd = ['pytest', '--suppress-no-test-exit-code']

    if seed:
        cmd.append(f'--randomly-seed={seed}')

    if not coverage:
        cmd.append('--no-cov')

    cmd0, cmd1 = cmd.copy(), cmd.copy()

    if coverage:
        cmd1.append('--cov-append')

    cmd0.append('asgi_signing_middleware')
    cmd1.append('tests')

    ctx.run(' '.join(cmd0), pty=True, echo=True)
    ctx.run(' '.join(cmd1), pty=True, echo=True)


@task
def safety(ctx):
    """Run Safety dependency vuln checker."""
    print('Safety check project requirements...')
    fd, requirements_path = mkstemp(prefix='asigm')
    os.close(fd)
    try:
        ctx.run(f'poetry export -f requirements.txt -o {requirements_path} --dev')
        ctx.run(f'safety check --full-report -r {requirements_path}')
    finally:
        os.remove(requirements_path)

    print('Safety check ReadTheDocs requirements (docs/readthedocs.requirements.txt)...')
    ctx.run('safety check --full-report -r docs/readthedocs.requirements.txt')


@task(
    aliases=['cc'],
    help={
        'complex': 'filter results to show only potentially complex functions (B+)',
    },
)
def cyclomatic_complexity(ctx, complex_=False):
    """Analise code Cyclomatic Complexity using radon."""
    # Run Cyclomatic Complexity
    cmd = 'radon cc -s -a'
    if complex_:
        cmd += ' -nb'
    ctx.run(f'{cmd} asgi_signing_middleware', pty=True)


@task(reformat, lint, tests, safety, aliases=['ci'])
def commit(ctx, amend=False):
    """Run all pre-commit commands and then commit staged changes."""
    cmd = ['git', 'commit']
    if amend:
        cmd.append('--amend')

    ctx.run(' '.join(cmd), pty=True)


def docs_venv(ctx: Context) -> None:
    """Ensure venv for the docs."""
    if not Path('tasks.py').exists():
        raise Exit("You can only run this command from the project's root directory", code=1)

    if Path('docs/.venv/bin/python').exists():
        return

    print('Creating docs venv...')
    with ctx.cd('docs'):
        ctx.run('python -m venv .venv')
        print('Installing dependencies...')
        with ctx.prefix('source .venv/bin/activate'):
            ctx.run('poetry install --no-ansi --no-root')


@contextmanager
def docs_context(ctx: Context) -> typing.Iterator[None]:
    """Context manager to do things in the docs dir with the proper virtualenv."""
    docs_venv(ctx)

    with ctx.cd('docs'):
        with ctx.prefix('source .venv/bin/activate'):
            yield


@task(
    help={
        'build': 'build the docs instead of serving them',
        'verbose': 'enable verbose output',
    },
)
def docs(ctx, build=False, verbose=False):
    """Serve the docs using mkdocs, alternatively building them."""
    args = ['mkdocs']

    if verbose:
        args.append('--verbose')

    if build:
        args.extend(['build', '--clean', '--strict'])
    else:
        args.append('serve')

    with docs_context(ctx):
        ctx.run(' '.join(args))


@task(
    help={'update': 'update dependencies first'},
    aliases=['docs-reqs'],
)
def docs_requirements(ctx, update=False):
    """Create docs requirements using poetry (overwriting existing one, if any).

    Additionally, if `update` is True then update dependencies first.
    """
    with docs_context(ctx):
        if update:
            print('Updating docs dependencies...')
            ctx.run('poetry install --no-ansi --remove-untracked')
            ctx.run('poetry update --no-ansi')

        print('Exporting docs requirements to readthedocs.requirements.txt...')
        ctx.run('poetry export -f requirements.txt -o readthedocs.requirements.txt')


def generate_trusted_comment_parts(
    *,
    timestamp: int,
    pubkey: str,
    email: str,
) -> typing.Tuple[typing.Tuple[str, str], ...]:
    """Generate a trusted comment for a minisign signature."""
    if not timestamp:
        timestamp = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())

    if not pubkey:
        with open('minisign.pub', 'rt', encoding='utf-8') as pubkeyfile:
            pubkey = pubkeyfile.readlines()[1].strip()

    if not email:
        # Encoded email to prevent spammers
        email = b64decode(codecs.decode('nTSwn2ShDTqgLJyfYzAioD', 'rot_13').encode()).decode()

    trusted_comment_parts = (
        ('timestamp', str(timestamp)),
        ('pubkey', pubkey),
        ('email', email),
    )

    return trusted_comment_parts


def generate_trusted_comment_from_parts(parts: typing.Sequence[typing.Tuple[str, str]]) -> str:
    """Generate a trusted comment from its parts."""
    return '\t'.join(f'{key}:{value}' for key, value in parts)


def generate_trusted_comment_for_file(
    file: Path,
    *,
    timestamp: int,
    pubkey: str,
    email: str,
) -> str:
    """Generate a trusted comment for a file minisign signature."""
    trusted_comment_parts = list(
        generate_trusted_comment_parts(
            timestamp=timestamp,
            pubkey=pubkey,
            email=email,
        ),
    )

    trusted_comment_parts.insert(1, ('file', file.name))

    return generate_trusted_comment_from_parts(trusted_comment_parts)


def generate_trusted_comment_for_tag(
    ctx,
    tag: str,
    *,
    timestamp: int,
    pubkey: str,
    email: str,
) -> str:
    """Generate a trusted comment for a tag minisign signature."""
    trusted_comment_parts = list(
        generate_trusted_comment_parts(
            timestamp=timestamp,
            pubkey=pubkey,
            email=email,
        ),
    )

    tag_hash_raw: Result = ctx.run(
        f'git tag --list --format "%(objectname)" "{tag}"',
        hide='out',
    )
    tag_hash = tag_hash_raw.stdout.strip()
    trusted_comment_parts.insert(1, ('object', tag_hash))

    return generate_trusted_comment_from_parts(trusted_comment_parts)


@task(
    help={
        'tag': 'git tag to sign',
        'trusted_comment': 'trusted comment to include in the signature',
        'untrusted_comment': 'untrusted comment to include in the signature',
        'seckey': 'full path to the signing secret key',
        'timestamp': 'unix timestamp in seconds to include in the trusted comment',
        'pubkey': 'encoded public key to include in the trusted comment',
        'email': 'signer email to include in the trusted comment',
        'force': 'true to force overwriting an existing note (defaults to false)',
    },
)
def sign_tag(  # pylint: disable=R0913
        ctx,
        tag,
        trusted_comment='',
        untrusted_comment='',
        seckey='',
        timestamp=0,
        pubkey='',
        email='',
        force=False,
):
    """Sign given tag with minisign.

    If trusted_comment is not specified, a default one is created composed of key:value
    separated by tabs, using the following information: timestamp (defaults to current
    timestamp), git object hash, signer public key (defaults to a hardcoded public key),
    signer email (defaults to a hardcoded email).

    If untrusted comment is not specified, a default hardcoded one is used.

    Note that this command requires the script `git-minisign-sign`. To fetch it, run:
    `git submodule sync --recursive && git submodule update --init --recursive --remote`

    Additionally, it requires minisign installed. For more information, refer to:
    https://jedisct1.github.io/minisign/
    """
    if not trusted_comment:
        trusted_comment = generate_trusted_comment_for_tag(
            ctx,
            tag,
            timestamp=timestamp,
            pubkey=pubkey,
            email=email,
        )

    if not untrusted_comment:
        untrusted_comment = 'signature from HacKan'

    args = [
        './git-minisign/sh/git-minisign-sign.sh',
        f'-t "{trusted_comment}"',
        f'-c "{untrusted_comment}"',
        f'-T "{tag}"',
    ]
    if seckey:
        args.append(f'-S "{seckey}"')
    if force:
        args.append('-f')

    ctx.run(' '.join(args), echo=True, pty=True)


@task(
    help={
        'file': 'file to sign',
        'trusted_comment': 'trusted comment to include in the signature',
        'untrusted_comment': 'untrusted comment to include in the signature',
        'seckey': 'full path to the signing secret key',
        'timestamp': 'unix timestamp in seconds to include in the trusted comment',
        'pubkey': 'encoded public key to include in the trusted comment',
        'email': 'signer email to include in the trusted comment',
    },
)
def sign_file(  # pylint: disable=R0913
    ctx,
    file,
    trusted_comment='',
    untrusted_comment='',
    seckey='',
    timestamp=0,
    pubkey='',
    email='',
):
    """Sign given file with minisign.

    If trusted_comment is not specified, a default one is created composed of key:value
    separated by tabs, using the following information: timestamp (defaults to current
    timestamp), file name, signer public key (defaults to a hardcoded public key), signer
    email (defaults to a hardcoded email).

    If untrusted comment is not specified, a default hardcoded one is used.

    Note that this command requires minisign installed. For more information, refer to:
    https://jedisct1.github.io/minisign/
    """
    if not trusted_comment:
        trusted_comment = generate_trusted_comment_for_file(
            Path(file),
            timestamp=timestamp,
            pubkey=pubkey,
            email=email,
        )

    if not untrusted_comment:
        untrusted_comment = 'signature from HacKan'

    args = [
        'minisign',
        '-S',
        f'-t "{trusted_comment}"',
        f'-c "{untrusted_comment}"',
        f'-m "{file}"',
    ]
    if seckey:
        args.append(f'-S "{seckey}"')

    ctx.run(' '.join(args), echo=True, pty=True)

    print('File signed as:', file + '.minisig')


@task
def verify_tag(ctx, tag):
    """Verify a tag signed by minisign."""
    ctx.run(f'./git-minisign/sh/git-minisign-verify.sh -T "{tag}"', echo=True)


@task
def verify_file(ctx, file):
    """Verify a file signed by minisign."""
    pubkeyfile = Path(__file__).parent / 'minisign.pub'
    ctx.run(f'minisign -Vm "{file}" -p {pubkeyfile}', echo=True)

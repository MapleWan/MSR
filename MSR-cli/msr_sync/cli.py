"""MSR-sync CLI 入口 — 使用 Click 框架定义所有子命令"""

import click

from msr_sync.core.exceptions import MSRError


@click.group()
def main():
    """MSR-sync: 统一管理多款 AI IDE 的 rules、skills、MCP 配置"""
    pass


@main.command()
@click.option("--merge", is_flag=True, help="合并已有 IDE 配置到统一仓库")
def init(merge):
    """初始化统一配置仓库"""
    from msr_sync.commands.init_cmd import init_handler

    try:
        init_handler(merge=merge)
    except MSRError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)


@main.command(name="import")
@click.argument("config_type", type=click.Choice(["rules", "skills", "mcp"]))
@click.argument("source")
def import_config(config_type, source):
    """导入配置到统一仓库"""
    from msr_sync.commands.import_cmd import import_handler

    try:
        import_handler(config_type=config_type, source=source)
    except MSRError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)


@main.command()
@click.option(
    "--ide",
    multiple=True,
    default=None,
    type=click.Choice(["trae", "qoder", "lingma", "codebuddy", "cursor", "all"]),
)
@click.option("--scope", default=None, type=click.Choice(["project", "global"]))
@click.option("--project-dir", default=None, type=click.Path())
@click.option(
    "--type",
    "config_type",
    default=None,
    type=click.Choice(["rules", "skills", "mcp"]),
)
@click.option("--name", default=None)
@click.option("--version", default=None)
def sync(ide, scope, project_dir, config_type, name, version):
    """同步配置到目标 IDE"""
    from msr_sync.commands.sync_cmd import sync_handler
    from msr_sync.core.config import get_config

    cfg = get_config()

    # 命令行未指定时使用配置值
    if ide is None or len(ide) == 0:
        ide = tuple(cfg.default_ides)
    if scope is None:
        scope = cfg.default_scope

    try:
        sync_handler(
            ide=ide,
            scope=scope,
            project_dir=project_dir,
            config_type=config_type,
            name=name,
            version=version,
        )
    except MSRError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)


@main.command(name="list")
@click.option(
    "--type",
    "config_type",
    default=None,
    type=click.Choice(["rules", "skills", "mcp"]),
)
def list_configs(config_type):
    """查看统一仓库中的配置列表"""
    from msr_sync.commands.list_cmd import list_handler

    try:
        list_handler(config_type=config_type)
    except MSRError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)


@main.command()
@click.argument("config_type", type=click.Choice(["rules", "skills", "mcp"]))
@click.argument("name")
@click.argument("version")
def remove(config_type, name, version):
    """删除指定配置版本"""
    from msr_sync.commands.remove_cmd import remove_handler

    try:
        remove_handler(config_type=config_type, name=name, version=version)
    except MSRError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)

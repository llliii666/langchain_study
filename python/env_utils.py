"""项目内的环境变量与依赖检查工具。

这个文件不是 LangChain 官方安装包的一部分，而是课程仓库自带的本地辅助模块。
它主要做两类事情：

1. 在模块导入时加载 `.env`，让 notebook 后续代码可以直接读取环境变量。
2. 提供几个辅助函数，用来检查环境变量和项目依赖是否配置正确。

需要特别注意：
- 只要执行 `import env_utils` 或 `from env_utils import ...`，
  下面的顶层代码就会立刻运行。
- 因此，这个模块是“带副作用的导入”：导入时会调用 `load_dotenv()`。
"""

import os
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from dotenv import dotenv_values
from dotenv import load_dotenv
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

# 在导入模块时立刻读取 `.env` 并写入当前 Python 进程的环境变量。
# `override=True` 表示：如果环境里已经有同名变量，也用 `.env` 中的值覆盖。
# 这能让 notebook 在导入本模块后，后续 `os.getenv(...)` 直接拿到配置。
load_dotenv(override=True)

# 下面几个变量是在模块导入时就从环境中读取出来的“快照”。
# 它们本身不是必须的，只是把常用 key 提前放成模块级变量，方便调试或引用。
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")

#这个函数将传入的变量先转为小写
#并且统一显示为****后四位
def summarize_value(value: str) -> str:
    """把敏感值脱敏后再显示。

    设计目的：
    - 检查变量“是否存在”时，经常希望看到一点点内容用于确认。
    - 但又不能把完整密钥直接打印到 notebook / 终端。

    处理规则：
    - 如果值是布尔字符串 true/false，则原样返回，便于直接观察开关状态。
    - 其他内容统一显示为 `****` + 最后 4 位。
    """
    #转小写
    lower = value.lower()
    #如果是bool则直接返回
    if lower in ("true", "false"):
        return lower
    #如果长度>4则返回****+后四位
    #如果长度小于等于四则返回****+密钥
    return "****" + value[-4:] if len(value) > 4 else "****" + value


def doublecheck_env(file_path: str):
    """根据 `.env` 文件中的键名，检查当前进程环境里是否已设置对应变量。

    这个函数不会再次“加载”环境变量，而是做“核对”：
    1. 先把 `.env` 文件解析成一个字典；
    2. 遍历其中的每个 key；
    3. 再到 `os.environ` 中检查这些 key 当前是否真的存在；
    4. 结果以脱敏方式打印出来。

    换句话说：
    - `.env` 文件在这里更像“检查清单”；
    - `os.environ` 才是当前 Python 进程实际在使用的环境变量来源。
    """
    # 如果用户还没有创建 `.env`，这里不报错中断，只给出提示。
    # 这样 notebook 仍然能继续执行，便于教学环境逐步配置。
    #检测环境中是否存在该文件(示例中为.env)
    if not os.path.exists(file_path):
        print(f"Did not find file {file_path}.")
        print("This is used to double check the key settings for the notebook.")
        print("This is just a check and is not required.\n")
        return

    # `dotenv_values` 会解析 `.env` 文件并返回字典，
    # 但它不会像 `load_dotenv` 那样把值写回 `os.environ`。
    #这里是dotenv包的函数,将文件中的内容以字典形式返回
    #dict={as:001,ad:002.....}
    parsed = dotenv_values(file_path)

    # 这里只遍历 `.env` 文件中定义过的 key。
    # 这样可以避免把系统中无关的环境变量全部打印出来。
    for key in parsed.keys():
        # 从当前进程环境中读取真实值，而不是直接信任 `.env` 文件中的文本。
        current = os.getenv(key)
        if current is not None:
            #如果该KEY存在则调用该函数,转为小写并遮住敏感值
            print(f"{key}={summarize_value(current)}")
        else:
            print(f"{key}=<not set>")


# ========== 基于 pyproject.toml 检查 Python 与依赖版本的工具 ==========
#
# 这一部分与 `.env` 无关。
# 它的用途是读取项目的 `pyproject.toml`，检查：
# - 当前 Python 版本是否满足 `requires-python`
# - 当前环境里安装的包是否满足 `dependencies` 的版本要求
#
# 依赖：
# - `tomllib`：解析 pyproject.toml（Python 3.11+ 内置）
# - `importlib.metadata`：读取已安装包的版本信息
# - `packaging`：解析依赖说明和版本约束


def _fmt_row(cols, widths):
    """把一行表格内容按固定宽度拼接成字符串。"""
    return " | ".join(str(c).ljust(w) for c, w in zip(cols, widths))


def doublecheck_pkgs(pyproject_path="pyproject.toml", verbose=False):
    """检查当前解释器和依赖包是否符合项目配置。

    检查思路：
    1. 读取 `pyproject.toml` 中 `[project]` 下的声明；
    2. 检查当前 Python 版本是否满足 `requires-python`；
    3. 遍历 `dependencies`，查看本环境里是否安装、版本是否匹配；
    4. 把问题项打印出来，方便用户定位环境问题。
    """
    p = Path(pyproject_path)
    if not p.exists():
        print(f"ERROR: {pyproject_path} not found.")
        return None

    # 读取 pyproject.toml，并取出项目级配置。
    with p.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    python_spec_str = project.get("requires-python") or ">=3.11"

    # 当前解释器版本，例如 3.11.7。
    py_ver = Version(
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # 判断当前 Python 是否满足项目要求。
    py_ok = py_ver in SpecifierSet(python_spec_str)

    # 读取 PEP 621 风格定义的依赖列表。
    deps = project.get("dependencies", [])
    if not deps:
        if verbose or not py_ok:
            print("No [project].dependencies found in pyproject.toml.")
            print(
                f"Python {py_ver} "
                f"{'satisfies' if py_ok else 'DOES NOT satisfy'} "
                f"requires-python: {python_spec_str}"
            )
            print(f"Executable: {sys.executable}")
        return None

    # 逐个检查依赖包。
    results = []
    problems = []
    for dep in deps:
        try:
            # 例如把 "langchain>=1.0.0" 解析成包名与版本约束。
            req = Requirement(dep)
            name = req.name
            spec = str(req.specifier) if req.specifier else "(any)"
        except Exception:
            # 如果某条依赖格式不标准，保底记录原始文本，
            # 避免整个检查流程中断。
            name, spec = dep, "(unparsed)"

        rec = {
            "package": name,
            "required": spec,
            "installed": "-",
            "path": "-",
            "status": "Missing",
        }

        try:
            # 查询当前环境中这个包的实际安装版本。
            installed_ver = metadata.version(name)
            rec["installed"] = installed_ver
            try:
                # 定位包安装路径，方便排查“到底读的是哪个环境里的包”。
                dist = metadata.distribution(name)
                rec["path"] = str(dist.locate_file(""))
            except Exception:
                rec["path"] = "(unknown)"

            # 如果依赖声明里写了版本范围，就进一步检查版本是否满足。
            if spec not in ("(any)", "(unparsed)") and any(op in spec for op in "<>="):
                sset = SpecifierSet(spec)
                if Version(installed_ver) in sset:
                    rec["status"] = "OK"
                else:
                    rec["status"] = "Version mismatch"
            else:
                rec["status"] = "OK"

        except metadata.PackageNotFoundError:
            # 如果包没装，保留默认记录即可。
            pass

        results.append(rec)
        if rec["status"] != "OK":
            problems.append(rec)

    # 默认只在有问题时输出；`verbose=True` 时无论是否有问题都打印详细信息。
    should_print = verbose or (not py_ok) or bool(problems)
    if should_print:
        # 先打印 Python 版本是否满足要求。
        print(
            f"Python {py_ver} "
            f"{'satisfies' if py_ok else 'DOES NOT satisfy'} "
            f"requires-python: {python_spec_str}"
        )

        # 构造一个简易文本表格展示依赖状态。
        headers = ["package", "required", "installed", "status", "path"]

        def short_path(s, maxlen=80):
            # 路径过长时从尾部截断，避免表格横向过宽。
            s = str(s)
            return s if len(s) <= maxlen else ("..." + s[-(maxlen - 3):])

        rows = [
            [
                r["package"],
                r["required"],
                r["installed"],
                r["status"],
                short_path(r["path"]),
            ]
            for r in results
        ]
        widths = [
            max(len(h), *(len(str(row[i])) for row in rows))
            for i, h in enumerate(headers)
        ]
        print(_fmt_row(headers, widths))
        print(_fmt_row(["-" * w for w in widths], widths))
        for row in rows:
            print(_fmt_row(row, widths))

        # 汇总问题项，但不强制指定用户必须使用哪种工具修复。
        if problems:
            print("\nIssues detected:")
            for r in problems:
                print(
                    f"- {r['package']}: {r['status']} "
                    f"(required {r['required']}, "
                    f"installed {r['installed']}, path {r['path']})"
                )

        if verbose or problems or not py_ok:
            print("\nEnvironment:")
            # 打印当前 Python 可执行文件路径，排查“解释器选错”非常有用。
            print(f"- Executable: {sys.executable}")

    return None

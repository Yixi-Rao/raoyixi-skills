# 代码注释自动生成指南

## 概述
本指南提供了一套完整的自动化流程，用于在 commit 之前检测新增和变更的代码，自动生成或更新函数注释（包括函数功能、入参、出参解释），确保代码文档的完整性和一致性。

## 操作目标
- 自动检测新增和变更的函数/方法
- 为缺少注释的函数生成标准注释
- 更新已变更函数的注释
- 确保注释格式符合项目规范
- 支持多种编程语言的注释风格

## 配置参数
```
支持语言: Python, JavaScript, TypeScript, Java, Go
注释风格: 
  - Python: Google Style, NumPy Style, reStructuredText
  - JavaScript/TypeScript: JSDoc
  - Java: JavaDoc
  - Go: GoDoc
检测范围: git diff 中的新增和变更函数
```

## 大模型执行指南

本指南专为大模型设计，提供逐步执行的代码注释生成流程。

### 🎯 执行原则
- **完整性**：注释应包含函数功能、所有参数、返回值说明
- **准确性**：注释应准确反映代码实际功能
- **一致性**：遵循项目统一的注释风格
- **可读性**：使用清晰、简洁的语言

### 🔍 步骤1：检测变更的代码

获取待提交的代码变更：

```bash
echo "=== 检测代码变更 ==="
# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD)

# 获取对比基础
if git rev-parse origin/$current_branch >/dev/null 2>&1; then
    base_commit=$(git merge-base HEAD origin/$current_branch)
else
    base_commit=$(git merge-base HEAD origin/master)
fi

echo "对比基础: $base_commit"
echo "当前提交: HEAD"

# 列出所有变更的文件
echo "=== 变更文件列表 ==="
git diff --name-only $base_commit HEAD

# 列出新增的文件
echo "=== 新增文件列表 ==="
git diff --name-only --diff-filter=A $base_commit HEAD
```

### 📋 步骤2：提取变更的函数

针对每个变更的文件，提取新增或修改的函数：

```bash
echo "=== 提取变更的函数 ==="
file_path="<file_path>"

# 获取该文件的 diff
git diff $base_commit HEAD -- $file_path > /tmp/file.diff

# 分析 diff 识别新增或修改的函数
# 对于 Python 文件
if [[ $file_path == *.py ]]; then
    echo "=== Python 函数检测 ==="
    # 提取新增的函数定义（以 + 开头的 def 行）
    grep "^+.*def " /tmp/file.diff
fi

# 对于 JavaScript/TypeScript 文件
if [[ $file_path == *.js ]] || [[ $file_path == *.ts ]]; then
    echo "=== JavaScript/TypeScript 函数检测 ==="
    # 提取新增的函数定义
    grep "^+.*function \|^+.*=> \|^+.*const.*= " /tmp/file.diff
fi
```

### 🔧 步骤3：读取函数代码

读取完整的函数实现以理解其功能：

```bash
echo "=== 读取函数完整代码 ==="
file_path="<file_path>"
function_name="<function_name>"

# 使用 ast-grep 或其他工具提取函数代码
# Python 示例
python3 << 'EOF'
import ast
import sys

def extract_function(file_path, func_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                # 获取函数起止行
                start_line = node.lineno
                end_line = node.end_lineno
                
                lines = source.split('\n')
                func_code = '\n'.join(lines[start_line-1:end_line])
                
                print(f"函数: {func_name}")
                print(f"起始行: {start_line}")
                print(f"结束行: {end_line}")
                print(f"代码:\n{func_code}")
                
                # 检查是否有 docstring
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant):
                        print(f"已有注释: {node.body[0].value.value}")
                        return True
                return False

if __name__ == '__main__':
    file_path = sys.argv[1]
    func_name = sys.argv[2]
    has_doc = extract_function(file_path, func_name)
    sys.exit(0 if has_doc else 1)
EOF
```

### 💡 步骤4：分析函数生成注释

根据函数代码分析并生成标准注释：

#### 4.1 Python 函数注释生成

**Google Style 示例**：
```python
def calculate_total(items: list[dict], tax_rate: float = 0.1, discount: float = 0) -> float:
    """
    计算商品总价，包含税费和折扣。

    该函数遍历商品列表，计算每个商品的小计，应用税率和折扣，
    最终返回总价。所有价格计算保留两位小数。

    Args:
        items (list[dict]): 商品列表，每个商品应包含 'price' 和 'quantity' 键
            示例: [{'price': 10.0, 'quantity': 2}, {'price': 5.0, 'quantity': 3}]
        tax_rate (float, optional): 税率，默认为 0.1 (10%)。取值范围 [0, 1]
        discount (float, optional): 折扣金额，默认为 0。应为非负数

    Returns:
        float: 计算后的总价，包含税费并扣除折扣，保留两位小数

    Raises:
        ValueError: 当 items 为空或包含无效数据时
        TypeError: 当参数类型不正确时

    Examples:
        >>> items = [{'price': 10.0, 'quantity': 2}, {'price': 5.0, 'quantity': 1}]
        >>> calculate_total(items, tax_rate=0.1, discount=5.0)
        22.50

    Note:
        - 税费在折扣前计算
        - 如果折扣大于总价，返回 0
    """
    # 函数实现...
```

**NumPy Style 示例**：
```python
def calculate_total(items, tax_rate=0.1, discount=0):
    """
    计算商品总价，包含税费和折扣。

    Parameters
    ----------
    items : list[dict]
        商品列表，每个商品应包含 'price' 和 'quantity' 键
    tax_rate : float, optional
        税率，默认为 0.1 (10%)，by default 0.1
    discount : float, optional
        折扣金额，默认为 0，by default 0

    Returns
    -------
    float
        计算后的总价，包含税费并扣除折扣

    Raises
    ------
    ValueError
        当 items 为空或包含无效数据时

    Examples
    --------
    >>> items = [{'price': 10.0, 'quantity': 2}]
    >>> calculate_total(items, tax_rate=0.1)
    22.0

    See Also
    --------
    calculate_subtotal : 计算小计
    apply_discount : 应用折扣

    Notes
    -----
    税费在折扣前计算
    """
    # 函数实现...
```

#### 4.2 JavaScript/TypeScript 注释生成

**JSDoc 示例**：
```javascript
/**
 * 计算商品总价，包含税费和折扣
 * 
 * 该函数遍历商品列表，计算每个商品的小计，应用税率和折扣，
 * 最终返回总价。所有价格计算保留两位小数。
 * 
 * @param {Array<{price: number, quantity: number}>} items - 商品列表
 * @param {number} [taxRate=0.1] - 税率，默认为 0.1 (10%)
 * @param {number} [discount=0] - 折扣金额，默认为 0
 * @returns {number} 计算后的总价，包含税费并扣除折扣
 * 
 * @throws {Error} 当 items 为空或包含无效数据时
 * 
 * @example
 * const items = [{price: 10.0, quantity: 2}, {price: 5.0, quantity: 1}];
 * const total = calculateTotal(items, 0.1, 5.0);
 * console.log(total); // 22.50
 * 
 * @since 1.0.0
 * @see {@link calculateSubtotal} 相关的小计计算函数
 */
function calculateTotal(items, taxRate = 0.1, discount = 0) {
    // 函数实现...
}
```

**TypeScript 类型注释示例**：
```typescript
/**
 * 商品接口定义
 */
interface Item {
    price: number;
    quantity: number;
}

/**
 * 计算商品总价，包含税费和折扣
 * 
 * @param items - 商品列表
 * @param taxRate - 税率，默认为 0.1
 * @param discount - 折扣金额，默认为 0
 * @returns 计算后的总价
 * 
 * @example
 * ```ts
 * const items: Item[] = [{price: 10, quantity: 2}];
 * const total = calculateTotal(items, 0.1, 5);
 * ```
 */
function calculateTotal(
    items: Item[], 
    taxRate: number = 0.1, 
    discount: number = 0
): number {
    // 函数实现...
}
```

#### 4.3 Java 注释生成

**JavaDoc 示例**：
```java
/**
 * 计算商品总价，包含税费和折扣。
 * 
 * <p>该方法遍历商品列表，计算每个商品的小计，应用税率和折扣，
 * 最终返回总价。所有价格计算保留两位小数。
 * 
 * @param items 商品列表，每个商品应包含价格和数量信息
 * @param taxRate 税率，取值范围 [0, 1]，默认为 0.1 (10%)
 * @param discount 折扣金额，应为非负数，默认为 0
 * @return 计算后的总价，包含税费并扣除折扣
 * @throws IllegalArgumentException 当 items 为 null 或空时
 * @throws IllegalArgumentException 当 taxRate 或 discount 为负数时
 * 
 * @see #calculateSubtotal(List)
 * @see #applyDiscount(double, double)
 * 
 * @since 1.0.0
 * @author Your Name
 */
public double calculateTotal(List<Item> items, double taxRate, double discount) {
    // 方法实现...
}
```

#### 4.4 Go 注释生成

**GoDoc 示例**：
```go
// CalculateTotal 计算商品总价，包含税费和折扣。
//
// 该函数遍历商品列表，计算每个商品的小计，应用税率和折扣，
// 最终返回总价。所有价格计算保留两位小数。
//
// 参数:
//   - items: 商品列表，每个商品应包含 Price 和 Quantity 字段
//   - taxRate: 税率，取值范围 [0, 1]
//   - discount: 折扣金额，应为非负数
//
// 返回值:
//   - float64: 计算后的总价，包含税费并扣除折扣
//   - error: 当输入无效时返回错误
//
// 示例:
//   items := []Item{{Price: 10.0, Quantity: 2}, {Price: 5.0, Quantity: 1}}
//   total, err := CalculateTotal(items, 0.1, 5.0)
//   if err != nil {
//       log.Fatal(err)
//   }
//   fmt.Printf("Total: %.2f\n", total)
//
// 注意:
//   - 税费在折扣前计算
//   - 如果折扣大于总价，返回 0
func CalculateTotal(items []Item, taxRate float64, discount float64) (float64, error) {
    // 函数实现...
}
```

### ✅ 步骤5：应用注释到代码

将生成的注释插入到函数定义之前：

```bash
echo "=== 应用函数注释 ==="
file_path="<file_path>"
function_line="<function_start_line>"  # 函数定义所在行号

# Python 示例：在函数定义后插入 docstring
python3 << 'EOF'
import sys

def insert_docstring(file_path, func_line, docstring):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 在函数定义行后插入 docstring
    # 需要保持正确的缩进
    func_def_line = lines[func_line - 1]
    indent = len(func_def_line) - len(func_def_line.lstrip())
    indent_str = ' ' * (indent + 4)  # 函数体缩进
    
    # 格式化 docstring
    doc_lines = ['"""' + docstring.split('\n')[0] + '\n']
    for line in docstring.split('\n')[1:]:
        if line.strip():
            doc_lines.append(indent_str + line + '\n')
    doc_lines.append(indent_str + '"""\n')
    
    # 插入到文件中
    lines.insert(func_line, indent_str + ''.join(doc_lines))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == '__main__':
    file_path = sys.argv[1]
    func_line = int(sys.argv[2])
    docstring = sys.argv[3]
    insert_docstring(file_path, func_line, docstring)
EOF
```

### 🔍 步骤6：验证注释质量

检查生成的注释是否符合规范：

```bash
echo "=== 验证注释质量 ==="
file_path="<file_path>"

# Python: 使用 pydocstyle 检查
if [[ $file_path == *.py ]]; then
    pydocstyle $file_path
fi

# JavaScript/TypeScript: 使用 eslint 检查
if [[ $file_path == *.js ]] || [[ $file_path == *.ts ]]; then
    eslint --rule 'jsdoc/require-jsdoc: error' $file_path
fi

# 通用检查：确保注释存在且格式正确
echo "=== 手动验证要点 ==="
echo "✓ 是否包含函数功能描述"
echo "✓ 是否描述了所有参数"
echo "✓ 是否描述了返回值"
echo "✓ 是否列出了可能的异常"
echo "✓ 格式是否符合项目规范"
```

### 📝 步骤7：批量处理所有变更

自动化处理所有变更的函数：

```bash
echo "=== 批量处理注释生成 ==="

# 获取所有变更的 Python 文件
changed_py_files=$(git diff --name-only $base_commit HEAD | grep "\.py$")

for file in $changed_py_files; do
    echo "处理文件: $file"
    
    # 提取文件中所有需要添加注释的函数
    # 这里需要实现一个完整的函数检测和注释生成流程
    
    # 1. 解析文件，找出所有函数
    # 2. 检查哪些函数缺少注释或注释不完整
    # 3. 为这些函数生成注释
    # 4. 将注释插入文件
    
    echo "✓ 完成: $file"
done

# 显示变更
git diff --stat
```

### ✅ 步骤8：提交带注释的代码

```bash
echo "=== 提交更新后的代码 ==="
# 添加所有更改（包括新增的注释）
git add .

# 显示变更内容
echo "=== 注释变更概览 ==="
git diff --cached --stat

# 提交
git commit -m "docs: add/update function documentation

- Added comprehensive docstrings for new functions
- Updated docstrings for modified functions
- Ensured all parameters and return values are documented"

echo "✓ 提交完成"
```

## 注释生成规则

### Python 函数注释规则

1. **必须包含的部分**：
   - 函数功能的简短描述（第一行）
   - 详细描述（可选，用于复杂函数）
   - Args: 所有参数的类型和说明
   - Returns: 返回值的类型和说明
   - Raises: 可能抛出的异常（如果有）

2. **可选部分**：
   - Examples: 使用示例
   - Note: 重要注意事项
   - See Also: 相关函数引用

3. **格式要求**：
   - 使用三引号 `"""` 包裹
   - 首行简短描述，句号结尾
   - 与函数定义保持相同缩进层级（内容缩进4空格）
   - 参数类型使用 Type Hints 时注释中可简化

### JavaScript/TypeScript 注释规则

1. **必须包含的部分**：
   - 函数功能描述
   - @param: 所有参数的类型和说明
   - @returns: 返回值的类型和说明
   - @throws: 可能抛出的异常（如果有）

2. **可选部分**：
   - @example: 使用示例
   - @see: 相关函数引用
   - @since: 版本信息
   - @deprecated: 废弃标记

3. **格式要求**：
   - 使用 `/** ... */` 包裹
   - 每个标签独占一行
   - 参数名使用 `{type} name - description` 格式

### 类和方法注释规则

**Python 类注释**：
```python
class ShoppingCart:
    """
    购物车管理类。

    该类负责管理用户的购物车，包括添加商品、删除商品、
    计算总价等功能。支持多种支付方式和优惠券。

    Attributes:
        items (list[Item]): 购物车中的商品列表
        user_id (str): 用户ID
        discount_code (str, optional): 优惠券代码

    Examples:
        >>> cart = ShoppingCart(user_id="user123")
        >>> cart.add_item(Item(name="Book", price=29.99))
        >>> cart.get_total()
        29.99

    Note:
        购物车数据不会自动持久化，需要调用 save() 方法保存
    """
    
    def __init__(self, user_id: str, discount_code: str = None):
        """
        初始化购物车。

        Args:
            user_id (str): 用户ID，不能为空
            discount_code (str, optional): 优惠券代码，默认为 None

        Raises:
            ValueError: 当 user_id 为空时
        """
        pass
```

## 自动化工具集成

### Pre-commit Hook 集成

创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: local
    hooks:
      - id: auto-doc-generator
        name: Auto Documentation Generator
        entry: python scripts/generate_docs.py
        language: python
        types: [python]
        pass_filenames: true
```

### 辅助脚本示例

**Python 注释生成脚本** (`scripts/generate_docs.py`):

```python
#!/usr/bin/env python3
"""
自动生成函数注释的辅助脚本
"""
import ast
import sys
from typing import List, Optional

def extract_function_info(node: ast.FunctionDef) -> dict:
    """
    提取函数的关键信息。

    Args:
        node: AST 函数节点

    Returns:
        包含函数信息的字典
    """
    info = {
        'name': node.name,
        'args': [],
        'returns': None,
        'docstring': ast.get_docstring(node)
    }
    
    # 提取参数信息
    for arg in node.args.args:
        arg_info = {
            'name': arg.arg,
            'annotation': ast.unparse(arg.annotation) if arg.annotation else None
        }
        info['args'].append(arg_info)
    
    # 提取返回类型
    if node.returns:
        info['returns'] = ast.unparse(node.returns)
    
    return info

def generate_docstring(func_info: dict) -> str:
    """
    根据函数信息生成标准注释。

    Args:
        func_info: 函数信息字典

    Returns:
        生成的 docstring
    """
    lines = [f"{func_info['name']} 函数。\n\n"]
    
    if func_info['args']:
        lines.append("Args:\n")
        for arg in func_info['args']:
            type_hint = f" ({arg['annotation']})" if arg['annotation'] else ""
            lines.append(f"    {arg['name']}{type_hint}: TODO: 添加参数描述\n")
        lines.append("\n")
    
    if func_info['returns']:
        lines.append(f"Returns:\n")
        lines.append(f"    {func_info['returns']}: TODO: 添加返回值描述\n")
    
    return ''.join(lines)

def process_file(file_path: str) -> bool:
    """
    处理单个文件，为缺少注释的函数生成注释。

    Args:
        file_path: 文件路径

    Returns:
        是否进行了修改
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    modified = False
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                func_info = extract_function_info(node)
                docstring = generate_docstring(func_info)
                print(f"生成注释: {func_info['name']}")
                print(docstring)
                modified = True
    
    return modified

if __name__ == '__main__':
    files = sys.argv[1:]
    any_modified = False
    
    for file_path in files:
        if process_file(file_path):
            any_modified = True
    
    sys.exit(1 if any_modified else 0)
```

## 完整执行示例

```bash
#!/bin/bash
echo "=== 代码注释自动生成流程 ==="

# 1. 获取变更的文件
echo "步骤 1: 检测变更文件"
current_branch=$(git rev-parse --abbrev-ref HEAD)
base_commit=$(git merge-base HEAD origin/master)
changed_files=$(git diff --name-only $base_commit HEAD | grep "\.py$")

echo "变更的 Python 文件:"
echo "$changed_files"

# 2. 对每个文件处理
for file in $changed_files; do
    echo ""
    echo "步骤 2: 处理文件 $file"
    
    # 3. 提取需要添加注释的函数
    echo "步骤 3: 提取函数列表"
    python3 scripts/extract_functions.py $file
    
    # 4. 生成注释
    echo "步骤 4: 生成函数注释"
    python3 scripts/generate_docs.py $file
    
    # 5. 验证注释
    echo "步骤 5: 验证注释质量"
    pydocstyle $file || echo "⚠️  注释格式需要调整"
done

# 6. 显示变更
echo ""
echo "步骤 6: 查看注释变更"
git diff --stat

# 7. 用户确认
echo ""
echo "步骤 7: 确认变更"
read -p "是否继续提交？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 8. 提交
    echo "步骤 8: 提交代码"
    git add .
    git commit -m "docs: add/update function documentation"
    echo "✓ 注释添加完成并已提交"
else
    echo "已取消提交"
fi
```

## 质量检查清单

### 注释生成前检查
- [ ] 已识别所有新增和变更的函数
- [ ] 已确定项目使用的注释风格
- [ ] 已理解函数的实际功能
- [ ] 已识别所有参数和返回值

### 注释生成中检查
- [ ] 功能描述清晰准确
- [ ] 所有参数都有说明
- [ ] 返回值有明确说明
- [ ] 异常情况有记录
- [ ] 格式符合规范

### 注释生成后检查
- [ ] 通过 pydocstyle/eslint 等工具检查
- [ ] 注释内容与代码实现一致
- [ ] 示例代码（如果有）可以运行
- [ ] 没有 TODO 或占位符留存

## 注意事项

### 质量原则
- **准确性优先**：注释必须准确反映代码功能
- **完整性要求**：所有公开函数都应有完整注释
- **简洁明了**：避免冗长的描述，重点突出
- **示例驱动**：复杂函数提供使用示例

### 特殊情况处理
- **私有函数**：可以简化注释，但核心逻辑需说明
- **装饰器**：需要说明装饰器的作用和影响
- **异步函数**：需要说明异步行为和注意事项
- **生成器**：需要说明 yield 的值和迭代行为

### 不要做的事情
- ❌ 不要生成无意义的通用注释
- ❌ 不要复制代码作为注释
- ❌ 不要使用不准确或误导性的描述
- ❌ 不要忽略异常和边界情况

### 最佳实践
- ✅ 在编写代码时就添加注释
- ✅ 代码变更时同步更新注释
- ✅ 使用类型提示减少注释需求
- ✅ 定期审查和改进注释质量
- ✅ 使用工具自动检查注释完整性

## 相关文档
- 代码提交规范：[autocommit.md](autocommit.md)
- Pre-commit 修复：[autofix.md](autofix.md)
- 大文件清理指南：[clean.md](clean.md)
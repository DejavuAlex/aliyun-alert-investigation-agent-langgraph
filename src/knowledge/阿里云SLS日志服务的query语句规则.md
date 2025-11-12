日志服务 Logstore 支持使用查询语句对存储在 Logstore 中的日志进行筛选。筛选结果可独立使用，也可以用于分析语句，进行更复杂的分析处理。本文介绍查询语句的语法结构，以及应用场景和具体示例。

## 基础语法

### 说明
通过 AI 智能生成查询与分析语句（Copilot）：日志服务提供 AI 智能辅助 SQL 语句的使用，支持自然语言生成 SQL、解释复杂 SQL、优化 SQL 语句。

查询语句和分析语句以 `|` 分割。其格式为：
查询语句 | 分析语句

text

查询语句可单独使用，分析语句必须与查询语句一起使用。即分析功能是基于查询结果或全量数据进行的。

> **重要**
> - 查询语句中建议不超过 30 个条件。
> - 分析语句中无需填写 FROM 子句和 WHERE 子句，默认分析当前 Logstore 中的数据。
> - 分析语句不支持使用 offset，不区分大小写，末尾无需加分号。

### 语句类型

| 语句类型 | 说明 |
|----------|------|
| 查询语句 | 查询条件，可以为关键词、数值、数值范围、空格、星号（`*`）等。如果为空格或星号（`*`），表示无过滤条件。 |
| 分析语句 | 对查询结果或全量数据进行计算和统计。日志服务支持的分析函数和语法，请参见：SQL 函数、SQL 子句、机器学习函数。 |

**查询和分析语句示例**：
| SELECT status, count(*) AS PV GROUP BY status


> **说明**
> 本文中涉及的查询示例的原始日志请参见调试。

## 查询语句编写思路

### 步骤一：确定查询方式

> **重要**
> - 如需对 Logstore 中的日志进行查询，则必须首先创建索引。
> - 如需要对某个字段进行分析（SELECT 语句），则必须创建字段索引。
> - 创建字段索引和全文索引的步骤，请参见创建索引。

不同的索引配置，会产生不同的查询和分析结果，如果同时创建了全文索引和字段索引，以字段索引的配置为准。

根据索引类型的不同，日志服务 Logstore 查询可分为**全文查询**和**字段查询**。

#### 全文查询
不针对具体的字段进行查询，支持通配符（`*`、`?`）和逻辑运算符（如 `and`、`or` 等）。

**查询语法**
keywords1 [ and | or | not ] keywords2 ...



**示例**
- 查询关键词为 GET 相关的日志：`GET`
- 查询关键词为 GET 或 POST 相关的日志：`GET or POST`
- 查询以 Jo 开头相关的日志：`Jo?`

#### 字段查询
针对具体字段名，支持类型化运算（如数值比较、正则表达式），需字段已建立索引。

> **重要**
> `indexname1` 是需要查询的字段名，当字段名、表名等专有名词中存在特殊字符（空格、中文等）、语法关键词（`and`、`or` 等）等内容时，则需要使用 `""`（双引号）包裹。

字段索引涉及 `long`、`double` 类型，可以使用比较运算符 `>`、`>=`、`<`、`<=`、`=`、`in`。

**查询语法**
indexname1 [ : | > | >= | < | <= | = | in ] keyword1 [ [ and | or | not ] indexname2 ... ]



**示例**
- 查询 `request_method` 为 GET 相关的日志：`request_method: GET`
- 查询 `request_time_msec` 大于 50 相关的日志：`request_time_msec>50`
- 查询 `request_method` 为 GET 且 `request_time_msec` 大于 50 相关的日志：`request_method: GET and request_time_msec>50`

### 步骤二：确定字段类型

编写查询语句时需要考虑字段类型的特点，合理使用运算符。

| 字段类型 | 说明 | 可用运算符 |
|----------|------|------------|
| text 类型 | 字符串类型的字段。开启全文索引后，日志服务默认将整条日志（除 `__time__` 以外所有字段）设置为 text 类型。 | `and`, `or`, `not`, `()`, `:`, `""`, `\`, `*`, `?` |
| long 和 double 类型 | 只有设置字段的数据类型为 long 或 double 后，才能通过数值范围查询该字段的值。 | `and`, `or`, `not`, `()`, `>`, `>=`, `<`, `<=`, `=`, `in` |
| JSON 类型 | 针对 JSON 对象中的字段，您可根据其值，将数据类型设置为 long、double 或 text，并开启统计功能。 | 根据 JSON 对象中的字段的类型使用不同的运算符 | 

注意：JSON字段引用方式,要用双引号包裹

### 步骤三：确定匹配模式

您可根据掌握的关键词信息及实际业务场景的需要灵活控制使用精准查询还是模糊查询。

| 查询方式 | 说明 | 示例 |
|----------|------|-------|
| 精确查询 | 使用完整的词进行查询。 | `host:example.com` 表示查询 host 字段值包含 example.com 的日志。<br>`PUT and cn-shanghai` 表示查询同时包含关键字 PUT 和 cn-shanghai 的日志。 |
| 模糊查询 | 在查询语句中指定一个 64 个字符以内的词，在词的中间或者末尾加上模糊查询关键字，即星号（`*`）或问号（`?`）。 | `request_time>60 and request_method:Ge*` 表示查询 request_time 字段值大于 60 且 request_method 字段值以 Ge 开头的日志。<br>`addr*` 表示在所有日志中查找以 addr 开头的 100 个词，并返回包含这些词的日志。 |

## 查询语句示例

### 普通查询示例

| 查询需求 | 查询语句 |
|----------|----------|
| 查询 GET 请求成功（状态码为 200~299）的日志 | `request_method:GET and status in [200 299]` |
| 查询来自非杭州地域的 GET 请求的日志 | `request_method:GET not region:cn-hangzhou` |
| 查询 GET 请求或 POST 请求的日志 | `request_method:GET or request_method:POST` |
| 查询非 GET 请求的日志 | `not request_method:GET` |
| 查询 GET 请求或 POST 请求成功的日志 | `(request_method:GET or request_method:POST) and status in [200 299]` |
| 查询 GET 请求或 POST 请求失败的日志 | `(request_method:GET or request_method:POST) not status in [200 299]` |
| 查询 GET 请求成功且请求时间小于 60 秒的日志 | `request_method:GET and status in [200 299] not request_time>=60` |
| 查询请求时间为 60 秒的日志 | `request_time:60` 或 `request_time=60` |
| 查询请求时间大于等于 60 秒，并且小于 200 秒的日志 | `request_time>=60 and request_time<200` 或 `request_time in [60 200)` |
| 查询 `request_time` 字段是否存在 | `request_time:*` |
| 查询 `request_time` 字段值为空或非法数字的日志 | `(request_time:"") or (not request_time > -10000000000)` |
| 查询包含 `request_time` 字段且字段值为数字的日志 | `request_time > -1000000000` |
| 查询包含 `and` 的日志 | `"and"` |
| 查询 `request method` 字段值是 PUT 的日志 | `"request method":PUT` |
| 查询日志主题为 HTTPS 或 HTTP 的日志 | `__topic__:HTTPS or __topic__:HTTP` |
| 查询采集于 192.0.2.1 主机的日志 | `"__tag__:__client_ip__":192.0.2.1` |
| 查询包含 192.168.XX.XX 的日志 | `* | select * from log where key like '192.168.%.%'` |
| 查询 `remote_user` 字段值不为空的日志 | `not remote_user:""` |
| 查询 `remote_user` 字段值为空的日志 | `remote_user:""` |
| 查询 `remote_user` 字段值不为 null 的日志 | `not remote_user:"null"` |
| 查询不存在 `remote_user` 字段的日志 | `not remote_user:*` |
| 查询存在 `remote_user` 字段的日志 | `remote_user:*` |
| 查询城市字段值不为上海的日志 | `not 城市:上海` |

### 进阶查询示例

#### 模糊查询

| 查询需求 | 查询语句 |
|----------|----------|
| 查询包含以 cn 开头的词的日志 | `cn*` |
| 查询 region 字段值是以 cn 开头的日志 | `region:cn*` |
| 查询 region 字段值包含 cn* 的日志 | `region:"cn*"` |
| 查询包含以 mozi 开头，以 la 结尾，中间还有一个字符的词的日志 | `mozi?la` |
| 查询包含以 mo 开头，以 la 结尾，中间包含零个、单个或多个字符的词的日志 | `mo*la` |
| 查询包含以 moz 开头的词和以 sa 开头的词的日志 | `moz* and sa*` |
| 查询 region 字段值以 hai 结尾的所有日志 | `*| select * from log where region like '%hai'` |
| 查询 message 字段值以 "get_time: 0. 开头的所有日志 | `*| select message where message like '"get_time: 0.%'` 或 `*| where message like '"get_time: 0.%'` |

#### 基于分词符的查询

| 查询需求 | 查询语句 |
|----------|----------|
| 查询 `http_user_agent` 字段值中包含 Chrome 的日志 | `http_user_agent:Chrome` |
| 查询 `http_user_agent` 字段值中包含 Linux 和 Chrome 的日志 | `http_user_agent:Linux and http_user_agent:Chrome` 或 `http_user_agent:"Linux Chrome"` |
| 查询 `http_user_agent` 字段值中包含 Firefox 或 Chrome 的日志 | `http_user_agent:Firefox or http_user_agent:Chrome` |
| 查询 `request_uri` 字段值包含 `/request/path-2` 的日志 | `request_uri:/request/path-2` |
| 查询 `request_uri` 字段值以 `/request` 开头，但不包含 `/file-0` 的日志 | `request_uri:/request* not request_uri:/file-0` |
| 完全匹配包含短语 `redo_index/1` 的日志 | `#"redo_index/1"` 或 `* | select * from log where key like 'redo_index/1'` |

### 特殊场景查询示例

#### 在查询语句中

| 查询需求 | 查询语句 |
|----------|----------|
| 查询 `request method` 字段值为 PUT 的日志 | `"request method":PUT` |
| 查询 `system error description` 字段值中包含 DB 的日志 | `"system error description":DB*` |
| 查询 `Authorization` 字段值为 `Bearer 12345` 的日志 | `"Authorization": "Bearer 12345"` |
| 分析 `errorContent` 字段值包含 `The body is not valid json string` 的日志 | `* | select * where errorContent like '%The body is not valid json string%'` |
| 查询采集于 192.0.2.1 主机的日志 | `"__tag__:__client_ip__":192.0.2.1` |

#### 在分析语句中

当字段名、表名等专有名词中存在特殊字符（空格、中文、`:`、`-` 等）、语法关键词（`and`、`or` 等）等内容时，需要使用 `""` 包裹。

表示字符串的字符必须使用 `''`（单引号）包裹。无符号包裹或被 `""`（双引号）包裹的字符表示字段名或列名。例如：`'status'` 表示字符串 status，`status` 或 `"status"` 表示日志字段 status。

**查询需求**：查询包含 192.168.XX.XX 的日志  
**查询语句**：
```sql
* | select * from log where key like '192.168.%.%'
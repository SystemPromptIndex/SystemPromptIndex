---
id: "JDOxyGent4J/JDOxyGent4J_-_docs_docs_zh_01_07_live_prompt"
company: "JDOxyGent4J"
product: "JDOxyGent4J - docs docs zh 01 07 live prompt"
category: "general-purpose"
source_file: "docs_docs_zh_01-07-live_prompt.md"
---

# 如何使用动态提示词（Live Prompts）

OxyGent 提供了动态提示词功能，允许您在运行时动态加载和更新智能体的提示词，无需重启应用程序，适用于需要频繁调整提示词的场景。

## 什么是动态提示词

动态提示词（Live Prompts）是一个存储在数据库中的提示词管理系统，支持：

- **自动集成**：LocalAgent 内置支持，无需额外配置
- **版本管理**：保存提示词的历史版本，支持回滚
- **备用机制**：当动态提示词不可用时，自动使用代码中的默认提示词
- **灵活开关**：可选择启用或禁用 live prompt 功能

## 基本用法

### 方式 1: 默认用法（推荐）

直接在 Agent 中设置 `prompt` 参数，系统会自动使用 live prompt 功能：

```java
ChatAgent.builder()
        .name("a_great_physicist")
        .prompt("""
                You are an AI agent embodying the intellectual persona of Albert Einstein.
                """)
        .llmModel("default_llm")
        .userLivePrompt(true)
        .build()
)
```

**工作原理：**

1. Agent 初始化时，自动从存储中查找键为 agentName + "_prompt" 既 `a_great_physicist_prompt` 的 live prompt
2. 如果找到且激活，使用存储中的提示词
3. 如果未找到，使用代码中的 `prompt` 参数作为后备

### 方式 2: 自定义 prompt_key

如果想使用不同的键名：

```java
ChatAgent.builder()
        .name("a_great_physicist")
        .prompt("""
                You are an AI agent embodying the intellectual persona of Albert Einstein.
                """)
        .promptKey("scientist_prompt")
        .llmModel("default_llm")
        .userLivePrompt(true)
        .build()
)
```

### 方式 3: 禁用 Live Prompt

如果不需要动态提示词功能（仅使用静态提示词）：

```java
ChatAgent.builder()
        .name("a_great_physicist")
        .prompt("""
                You are an AI agent embodying the intellectual persona of Albert Einstein.
                """)
        .promptKey("scientist_prompt")
        .llmModel("default_llm")
        .userLivePrompt(false)
        .build()
)
```

## 参数说明

### LocalAgent 的 Live Prompt 相关参数

- **`prompt`** (str): 提示词内容，作为后备使用
- **`promptKey`** (str, 可选): Live prompt 的键名
  - 默认值: `"{agent_name}_prompt"`
  - 用于从存储中查找动态提示词
- **`useLivePrompt`** (bool, 可选): 是否启用 live prompt 功能
  - 默认值: `True`
  - 设为 `False` 时只使用代码中的 `prompt` 参数

## 完整示例

以下是一个完整的使用动态提示词的示例：

```java
import com.jd.oxygent.core.oxygent.oxy.BaseOxy;
import com.jd.oxygent.core.oxygent.oxy.agents.ChatAgent;
import com.jd.oxygent.core.oxygent.oxy.agents.ReActAgent;
import com.jd.oxygent.core.oxygent.oxy.llms.HttpLlm;
import com.jd.oxygent.core.oxygent.oxy.mcp.StdioMCPClient;
import com.jd.oxygent.core.oxygent.samples.server.ServerApp;
import com.jd.oxygent.core.oxygent.samples.server.masprovider.engine.annotation.OxySpaceBean;
import com.jd.oxygent.core.oxygent.samples.server.utils.GlobalDefaultOxySpaceMapping;
import com.jd.oxygent.core.oxygent.utils.EnvUtils;

import java.util.Arrays;
import java.util.List;

/**
 * Demo application showing the use of OxyGent with live prompts
 *
 * @author OxyGent Team
 * @version 1.0.10.4
 * @since 1.0.10.4
 */
public class DemoLivePrompt {

    /**
     * Get default OxySpace configuration
     *
     * <p>Configuration includes:</p>
     * <ul>
     *   <li><strong>HttpLlm</strong>: HTTP LLM service configuration</li>
     *   <li><strong>ChatAgent</strong>: Chat agent configured with input processing function</li>
     * </ul>
     *
     * <p>Note: ChatAgent uses funcProcessInput to process input,
     * allowing test messages to be sent before agent processes requests.</p>
     *
     * @return List of BaseOxy containing LLM and ChatAgent
     */
    @OxySpaceBean(value = "demoLivePrompt", defaultStart = true, query = "Who are you")
    public static List<BaseOxy> getDefaultOxySpace() {
        var apiKey = EnvUtils.getEnv("OXY_LLM_API_KEY");
        var baseUrl = EnvUtils.getEnv("OXY_LLM_BASE_URL");
        var modelName = EnvUtils.getEnv("OXY_LLM_MODEL_NAME");

        return Arrays.asList(
                // 1. HTTP LLM Configuration
                HttpLlm.builder()
                        .name("default_llm")
                        .apiKey(apiKey)
                        .baseUrl(baseUrl)
                        .modelName(modelName)
                        .timeout(30)
                        .build(),
                // 2. Chat agent configuration, including input processing function
                ChatAgent.builder()
                        .name("a_great_physicist")
                        .prompt("""
                                You are an AI agent embodying the intellectual persona of Albert Einstein.
                                """)
                        .promptKey("scientist_prompt")
                        .llmModel("default_llm")
                        .userLivePrompt(true)
                        .build()
        );
    }

    public static void main(String[] args) throws Exception {
        var currentClassName = Thread.currentThread().getStackTrace()[1].getClassName();
        GlobalDefaultOxySpaceMapping.searchCurrentThreadStackAnnotationOxySpaceName(currentClassName);
        ServerApp.main(args);
    }
}
```

## 热更新提示词

修改存储中的提示词后，需要手动触发热更新才能生效：

### 方法 1: 通过 Agent 实例

```java
# 热更新提示词
boolean success = mas.getOxyByName("a_great_physicist").reloadPrompt();
if success:
    print("提示词已更新")
```

### 方法 2: 通过便捷函数

```java
# 热更新单个 agent
boolean success = DynamicAgentManager.getInstance().updateAgentPrompt("a_great_physicist");

# 热更新使用指定 prompt_key 的所有 agents
boolean success = DynamicAgentManager.getInstance().hotReloadPrompt("scientist_prompt");

# 热更新所有 agents
boolean success = DynamicAgentManager.getInstance().hotReloadAllPrompts();
```

### 方法 3: 在保存时自动触发（推荐）

在提示词管理平台的保存 API 中自动触发热更新：

```java
boolean success = PromptManager.getInstance().savePrompt(promptKey, promptContent, description, category, agentType, 1, isActive, tags, createdBy);
```

## 配置要求

动态提示词功能需要配置数据库连接：

- 支持 Elasticsearch 作为主要存储
- 当 ES 不可用时，自动回退到 LocalEs（本地文件存储）
- 通过 `Config` 系统配置数据库连接参数

### 配置参数

在 `config.json` 中添加以下配置：

```json
{
  "live_prompt": {
    "es_polling_interval": 2  // ES 轮询间隔（秒），默认值为 2
  }
}
```

**参数说明**：

- **`es_polling_interval`**：ES 轮询间隔，单位为秒
  - 默认值：`2`
  - 适用场景：多实例部署时，控制不同实例间提示词同步的延迟时间
  - 建议：根据实际需求调整，值越小同步越快，但会增加 ES 查询频率

**通过代码配置**：

```java
import com.jd.oxygent.core.Config;

# 设置 ES 轮询间隔为 5 秒
Config.getLivePrompt().setEsPollingInterval(5);

# 获取当前配置
int interval = Config.getLivePrompt().getEsPollingInterval(5);
```

### 多实例部署要求

**重要**：如果在多实例部署环境下使用动态提示词功能，**必须配置 Elasticsearch**。

系统会根据配置自动检测同步机制：

1. **ES 轮询（推荐）**：
   
   - 配置要求：远程 Elasticsearch
   - 优点：无需额外组件，基于现有 ES 存储
   - 延迟：默认 2 秒轮询间隔（可通过 `live_prompt.es_polling_interval` 配置）

2. **无同步机制**：
   
   - 当 ES 为本地配置或未配置时
   - **警告**：多实例环境下缓存不一致，不建议使用 live_prompt
   - 仅适用于单实例部署

## 注意事项

1. **向后兼容**：现有代码无需修改，默认启用 live prompt 功能
2. **多实例部署**：
   - 必须配置远程 ES 以保证缓存一致性
   - 未配置时，多实例间缓存可能不一致
3. **性能考虑**：
   - 提示词在初始化时从数据库加载一次，之后使用缓存
   - 禁用 live prompt 的 Agent 性能略好（不查询数据库）
   - ES 轮询模式：默认 2 秒延迟（可通过 `live_prompt.es_polling_interval` 调整）
   - 轮询间隔越小，同步越快，但会增加 ES 查询负载
4. **错误处理**：当 live prompt 系统不可用时，自动使用代码中的 `prompt` 参数，确保系统稳定运行
5. **版本管理**：系统会自动保存提示词的修改历史，支持版本回滚
6. **灵活控制**：可以为每个 Agent 单独设置是否启用 live prompt

## 常见问题

### Q1: 如何禁用 live prompt 功能？

**A**: 设置 `use_live_prompt=False` 参数。

### Q2: prompt_key 的默认值是什么？

**A**: `{agent_name}_prompt`，例如 Agent 名为 `a_great_physicist`，则默认 `prompt_key` 为 `a_great_physicist_prompt`。

### Q3: 如果存储中没有提示词会怎样？

**A**: 会使用代码中的 `prompt` 参数作为后备。

### Q4: live prompt 会影响性能吗？

**A**: 影响很小。只在初始化时访问一次数据库，之后使用缓存。如有极高性能要求，可禁用 live prompt。

### Q5: 多实例部署时如何保证提示词同步？

**A**: 必须配置远程 Elasticsearch。系统会通过 ES 轮询自动同步：

- ES 轮询：默认 2 秒延迟同步（可配置）
- 本地配置：无法跨实例同步，会显示警告

### Q6: 如何知道当前使用的同步机制？

**A**: 启动时查看日志输出：

- `ES polling enabled for remote hosts: xxx` - 使用 ES 轮询
- `ES polling not available` - 无同步机制（仅单实例）
- `Starting ES polling with Xs interval` - 显示当前轮询间隔

### Q7: 如何调整 ES 轮询间隔？

**A**: 通过以下两种方式：

**方式 1：在配置文件中设置**

```json
{
  "live_prompt": {
    "es_polling_interval": 5
  }
}
```

**方式 2：通过代码设置**

```java
import com.jd.oxygent.core.Config;

# 设置 ES 轮询间隔为 5 秒
Config.getLivePrompt().setEsPollingInterval(5);
```

## 相关文档

- [Live Prompts 集成指南](./live_prompts_integration.md) - 详细的集成说明
- [Live Prompts 热更新指南](./live_prompts_hot_reload.md) - 热更新使用方法
- [use_live_prompt 开关参考](./use_live_prompt_reference.md) - 开关参数详解

[上一章：如何设置缓存消息方式](./01-06-select_cache.md)
[下一章：注册一个工具](./02-01-register_single_tool.md)
[回到首页](./readme.md)

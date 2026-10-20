-- 默认目标根模块：只 import 彼此不冲突的模块；
-- Upper / Upper2 通过 lakefile 的 defaultTargets 单独构建（二者都定义 Mj.reqOk，无法合并到一个环境）。
import Mj.Basic
import Mj.Protocol
import Mj.Lemma
import Mj.Disproof
import Mj.Bridge

**AA**

[2:23 PM](https://matrixport.slack.com/archives/D07E0AXUBF1/p1749450217857929)

hi XX， 我在看\<DOC\>，托管方面有几个基础问题想请教下？

之前多签使用了智能合约，智能合约必定需要联网（连接主链）是吗？ 为啥多签需要使用智能合约和联网，不能几台机器拆分key之后只是本地聚合做签名吗

**XX**

[2:27 PM](https://matrixport.slack.com/archives/D07E0AXUBF1/p1749450474333379)

ETH没有原生的多签能力，如果需要提供可证明的多签能力只能用智能合约。你说的拆分Key搞多签的方式是MPC，我们不在\<PROJ\>使用MPC的主要原因为：

- MPC没有一个标准代码实现，对应的代码如果需要审计会花费更多的精力。

- 标准和代码没经过历史的验证，可能会有漏洞。

**AA**

[2:30 PM](https://matrixport.slack.com/archives/D07E0AXUBF1/p1749450621865479)

噢， 原来之前的多签不是这种Multi-Party Computation， 而是借助ETH 智能合约搞的。

所以现在要把ETH 智能合约去掉， 只能搞单签了

**XX**

[2:31 PM](https://matrixport.slack.com/archives/D07E0AXUBF1/p1749450669342349)

是的

**AA**

[2:33 PM](https://matrixport.slack.com/archives/D07E0AXUBF1/p1749450830057269)

了解了，多谢!

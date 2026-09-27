# Aeron archive different moving parts

## Sheet1

| Writer |  | Reader |
|---|---|---|
| Pub |  | Sub |
| ArchiveServer |  | ArchiveClient |
| ControlRequestChannel | 发送命令的channel (request, replay, stop) |  |
| ControlResponseChannel | 接收命令的channel |  |

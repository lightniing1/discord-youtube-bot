# Bot de Música para Discord

Este repositório contém um bot de música para Discord desenvolvido em Python. O bot permite que os usuários reproduzam músicas do YouTube, gerenciem filas e controlem a reprodução em canais de voz.

## Funcionalidades

- Reproduza músicas fornecendo uma URL ou termo de busca.
- Gerencie uma fila de músicas.
- Pule, pare e limpe a reprodução.
- Registre comandos do bot e respostas para monitoramento e depuração.

## Requisitos

- Python 3.8+
- Token da API do Discord
- ffmpeg
- Bibliotecas Python necessárias (listadas em `requirements.txt`):
  - `discord`
  - `PyNaCl`
  - `yt-dlp`
  - `aiohttp`

## Instalação

1. Clone o repositório ou baixe o script.
2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```
4. Preencha o `bot.run("")` com o seu token do bot do Discord.

## Uso

1. Execute o bot:
   ```bash
   python bot.py
   ```
2. Adicione o bot ao seu servidor Discord com as permissões apropriadas.
3. Use os seguintes comandos em um canal de texto:

### Comandos

- **`!play <query>`**: Reproduz uma música a partir de uma URL ou termo de busca.
  - Exemplo: `!play never gonna give you up`

- **`!skip`**: Pule a música atual.

- **`!stop`**: Pare a reprodução e limpe a fila.

- **`!queue`**: Mostra a fila de músicas atual.

- **`!commands`**: Lista todos os comandos disponíveis.

## Estrutura de Arquivos

- **`bot.py`**: Script principal do bot de música.
- **`downloads/`**: Diretório para armazenar os arquivos de áudio baixados.
- **`logs/`**: Diretório para armazenar os arquivos de log.

## Logs

O bot registra todos os comandos e respostas em um arquivo localizado no diretório `logs`. Os arquivos de log são nomeados com o formato de data `bot_YYYYMMDD.log`.

## Solução de Problemas

- Certifique-se de que o bot tem permissões para conectar e falar em canais de voz.
- Se a reprodução falhar, verifique os logs para obter detalhes do erro.

## Contribuindo

Sinta-se à vontade para fazer um fork deste repositório e enviar pull requests com melhorias ou novos recursos.

## Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

# SYSTEMS
システム関連はここに記載しています。

## ネットワーク関連
Tailscaleでtailnet構築中。Tailscaleにログインすることで、下記「ファイルサーバー」内のシステムを使用可能。

- 連携アカウント：GitHub
    - user: REIJIKAMIO

## サーバー情報

### XSERVER
#### アカウント
- [XSERVER HOMEPAGE](https://www.xserver.ne.jp/)
    - user: king03.create@gmail.com
    - pass: いつもの

#### ftpアカウント
ファイルの転送はftpコマンドで。

- server: sv16253.xserver.jp
- account: king03.create@gmail.com
- pass: いつもの

### ホームサーバー
ProxMoxでサーバーを立てて運用中。

- ip: 192.168.1.120: [pve管理画面](http://192.168.1.120:8006)
    - user: root
    - pass: いつもの

#### ファイルサーバー（SMB）用
- コンテナID: 100
    - user: root
    - pass: いつもの
- ip: 192.168.1.130
- NAS
    - /mnt/archives
    - /mnt/medias
    - /mnt/workstation

#### LinuxMint
Mint内でDocker経由でクラウド環境構築中。Tailscaleで連携中、上記PVEもしくはRustDeskで遠隔操作可能。

- コンテナID: 200
    - user: reijikamio
    - pass: いつもの
- ip: 192.168.1.200
    - 8000: [MkDocs](http://192.168.1.200:8000) (repo srv.mkdocs)
    - 8080: [nextcloud](http://192.168.1.200:8080) (repo proj.reiji.rab)
    - 8081: [code server](http://192.168.1.200:8081) (repo proj.reiji.rab)

##### キーボード入力について
- 英字キーボードの場合
    - 日本語／アルファベットの切り替え：バッククォート
    - 日本語／USキーボード（配列）の切り替え：上記アルファベット入力中にCtrl+Shift(日本語入力中は切り替え不可)

## 編集ファイル関連
GitHubにて以下リポジトリを管理。CODE SERVERの`git`ディレクトリ、LinuxMintの`~/Develops/git`上で同様のリポジトリを管理・編集中。編集ファイルはここにしかないため、CODE SERVERもしくはLinuxMint上で編集した後は、定期的にpushすること。

### ユーザー情報
- user: REIJIKAMIO
- pass: いつもの
### リポジトリ
#### プロジェクト関連
##### proj.reiji.lab ([GitHub]((https://github.com/REIJIKAMIO/proj.reiji.lab)))
システムやWEB、アプリのプロトタイプを作成する場所。本リポジトリ内で試作し、安定稼働が見込まれた際には本稼働を行う。

##### proj.tamamori-jinja ([GitHub](https://github.com/REIJIKAMIO/proj.tamamori-jinja))
魂守神社関連の作業ファイルを格納しておく場所。

##### proj.xover.works ([GitHub](https://github.com/REIJIKAMIO/proj.xover.works))
デザイン業務関連の作業ファイルを格納しておく場所。

##### proj.kisarazu.kankou ([GitHub](https://github.com/REIJIKAMIO/proj.kisarazu.kankou))
観光協会関連の作業ファイルを格納しておく場所。

#### サービス関連
##### srv.mkdocs ([GitHub](https://github.com/REIJIKAMIO/srv.mkdocs))
mkdocs用のリポジトリ。composeとdocsファイルを全て格納。
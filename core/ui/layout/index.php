<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, interactive-widget=resizes-content">
    <link rel="stylesheet" href="/css/main.css">
    <script src="/js/change_view.js" defer></script>
    <title>R-CORE</title>
</head>
<body>
    <header>
        <h1>
            <a href="/">R-CORE</a>
        </h1>
        <div>
            <ul>
                <li class="view-toggle"><a href="" id="view_toggle">表示切替</a></li>
                <li class="view-all"><a href="" id="view_all">全表示</a></li>
            </ul>
        </div>
    </header>
    <main>
        <div class="wrapper">
            <div class="container-main r-box">
                <div class="container-nav" id="container_nav">
                    <div class="nav-top r-box">

                    </div>
                    <div class="nav-bottom r-box">
                        <?php include_once('./nav-list.php');?>
                    </div>
                </div>
                <div class="container-viewer r-box" id="container_viewer">
                    <iframe src="http://192.168.1.200:8000/" frameborder="0" name="container-frame"></iframe>
                </div>
            </div>
        </div>
    </main>
    <footer>
    </footer>
</body>
</html>
#!/usr/bin/bash

ACTION="${1:-}"
APP="${2:-}"

DIR="$(cd "$(dirname "$0")" && pwd)"
APPS_DIR="$DIR/../apps"

# ----------------------------------------
# 引数チェック
# ----------------------------------------

if [ -z "$ACTION" ] || [ -z "$APP" ]; then
    echo "Usage: $0 up|down|status|build|restart|rebuild <app-name|all>"
    exit 1
fi


# ----------------------------------------
# 1アプリを操作する関数
# ----------------------------------------

run_app() {
    local action="$1"
    local app="$2"
    local app_dir="$APPS_DIR/$app"

    if [ ! -d "$app_dir" ]; then
        echo "Unknown app: $app"
        return 1
    fi

    # mdnestの場合（例外処理）
    if [ "$app" = "mdnest" ]; then
        case "$action" in
            up)
                echo "Starting: mdnest"
                (cd "$app_dir" && ./mdnest-server start)
                ;;

            down)
                echo "Stopping: mdnest"
                (cd "$app_dir" && ./mdnest-server stop)
                ;;

            restart)
                echo "Restarting: mdnest"
                (cd "$app_dir" && ./mdnest-server restart)
                ;;

            rebuild)
                echo "Rebuilding: mdnest"
                (cd "$app_dir" && ./mdnest-server rebuild)
                ;;

            status)
                (cd "$app_dir" && ./mdnest-server status)
                ;;

            *)
                echo "Unsupported action for mdnest: $action"
                return 1
                ;;
        esac

        return
    fi

    # 通常処理
    
    if [ ! -f "$app_dir/compose.yaml" ]; then
        echo "compose.yaml not found: $app"
        return 1
    fi
    
    case "$action" in

        up)
            echo "Starting: $app"
            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                up -d
            ;;

        down)
            echo "Stopping: $app"
            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                down
            ;;

        status)
            echo "===== $app ====="
            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                ps
            ;;

        build)
            echo "Building: $app"
            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                build
            ;;

        restart)
            echo "Restarting: $app"

            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                down

            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                up -d
            ;;

        rebuild)
            echo "Rebuilding: $app"

            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                down

            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                build

            docker compose \
                --project-directory "$app_dir" \
                -f "$app_dir/compose.yaml" \
                up -d
            ;;

        *)
            echo "Unknown action: $action"
            return 1
            ;;

    esac
}


# ----------------------------------------
# all
# ----------------------------------------

if [ "$APP" = "all" ]; then

    for app_dir in "$APPS_DIR"/*; do

        # ディレクトリでなければ無視
        [ -d "$app_dir" ] || continue

        # compose.yaml がなければ無視
        [ -f "$app_dir/compose.yaml" ] || continue

        app="$(basename "$app_dir")"

        run_app "$ACTION" "$app"

    done

else

    run_app "$ACTION" "$APP"

fi


document$.subscribe(function () {

  // ========================================================
  // 前ページの処理を掃除
  // Material Instant Loading対策
  // ========================================================

  if (window.__h2PagesCleanup) {
    window.__h2PagesCleanup();
  }


  const controller =
    new AbortController();

  const signal =
    controller.signal;

  const observers = [];


  const mobileQuery =
    window.matchMedia(
      "(max-width: 767px)"
    );


  const reducedMotionQuery =
    window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );


  const footer =
    document.querySelector(
      ".md-footer"
    );


  const header =
    document.querySelector(
      ".md-header"
    );


  // ========================================================
  // 共通
  // ========================================================

  function isMobile() {
    return mobileQuery.matches;
  }


  function motion() {
    return reducedMotionQuery.matches
      ? "auto"
      : "smooth";
  }


  function clamp(
    value,
    min,
    max
  ) {

    return Math.max(
      min,
      Math.min(
        value,
        max
      )
    );

  }


  // ========================================================
  // Cleanup
  // ========================================================

  function cleanup() {

    controller.abort();


    observers.forEach(
      (observer) => {
        observer.disconnect();
      }
    );


    document.documentElement
      .classList
      .remove(
        "h2-reader-active"
      );


    document.documentElement
      .style
      .removeProperty(
        "--mobile-footer-height"
      );


    document.documentElement
      .style
      .removeProperty(
        "--mobile-indicator-height"
      );


    document.documentElement
      .style
      .removeProperty(
        "--mobile-reader-floor"
      );

  }


  window.__h2PagesCleanup =
    cleanup;


  // ========================================================
  // Footer高さ
  //
  // ブログ等でも必要
  // ========================================================

  function measureFooter() {

    if (
      !isMobile()
      ||
      !footer
    ) {

      document.documentElement
        .style
        .removeProperty(
          "--mobile-footer-height"
        );

      return;

    }


    const height =
      footer
        .getBoundingClientRect()
        .height;


    document.documentElement
      .style
      .setProperty(
        "--mobile-footer-height",
        `${height}px`
      );

  }


  measureFooter();


  window.addEventListener(
    "resize",
    measureFooter,
    {
      signal
    }
  );


  if (
    footer
    &&
    "ResizeObserver" in window
  ) {

    const footerObserver =
      new ResizeObserver(
        measureFooter
      );


    footerObserver.observe(
      footer
    );


    observers.push(
      footerObserver
    );

  }


  // ========================================================
  // 本文
  // ========================================================

  const content =
    document.querySelector(
      ".md-content__inner"
    );


  if (!content) {
    return;
  }


  // ========================================================
  // ブログではReader化しない
  // ========================================================

  const isBlogPost =
    Boolean(
      document.querySelector(
        ".md-content--post"
      )
    );


  if (isBlogPost) {
    return;
  }


  // ========================================================
  // 二重初期化防止
  // ========================================================

  if (
    content.querySelector(
      ".h2-pages"
    )
  ) {
    return;
  }


  // ========================================================
  // H2を検索
  // ========================================================

  const children =
    Array.from(
      content.children
    );


  const firstH2Index =
    children.findIndex(
      (element) =>
        element.tagName === "H2"
    );


  if (
    firstH2Index === -1
  ) {
    return;
  }


  // ========================================================
  // Reader起動
  // ========================================================

  document.documentElement
    .classList
    .add(
      "h2-reader-active"
    );


  // ========================================================
  // 構造
  //
  // h2-pages       ← viewport
  //   h2-pages__track
  //     h2-page
  //     h2-page
  //     h2-page
  //
  // overflow横スクロールではなく
  // trackをtransformで動かす
  // ========================================================

  const wrapper =
    document.createElement(
      "div"
    );


  wrapper.className =
    "h2-pages";


  const pageTrack =
    document.createElement(
      "div"
    );


  pageTrack.className =
    "h2-pages__track";


  wrapper.appendChild(
    pageTrack
  );


  let currentPage = null;
  let currentInner = null;


  children
    .slice(
      firstH2Index
    )
    .forEach(
      (element) => {

        if (
          element.tagName === "H2"
        ) {

          currentPage =
            document.createElement(
              "section"
            );


          currentPage.className =
            "h2-page";


          currentInner =
            document.createElement(
              "div"
            );


          currentInner.className =
            "h2-page__inner";


          currentPage.appendChild(
            currentInner
          );


          pageTrack.appendChild(
            currentPage
          );

        }


        if (
          currentInner
        ) {

          currentInner.appendChild(
            element
          );

        }

      }
    );


  const pages =
    Array.from(
      pageTrack.querySelectorAll(
        ".h2-page"
      )
    );


  const pageInners =
    Array.from(
      pageTrack.querySelectorAll(
        ".h2-page__inner"
      )
    );


  if (
    pages.length === 0
  ) {

    document.documentElement
      .classList
      .remove(
        "h2-reader-active"
      );

    return;

  }


  // ========================================================
  // タイトル
  // ========================================================

  const pageTitles =
    pages.map(
      (page, index) => {

        const h2 =
          page.querySelector(
            "h2"
          );


        return (
          h2?.textContent?.trim()
          ||
          `Page ${index + 1}`
        );

      }
    );


  // ========================================================
  // TOC
  // ========================================================

  const toc =
    document.createElement(
      "nav"
    );


  toc.className =
    "page-toc";


  toc.setAttribute(
    "aria-label",
    "ページ目次"
  );


  const tocItems = [];


  pageTitles.forEach(
    (title, index) => {

      const button =
        document.createElement(
          "button"
        );


      button.type =
        "button";


      button.className =
        "page-toc-item";


      button.textContent =
        title;


      button.setAttribute(
        "aria-label",
        `${index + 1}ページ目: ${title}`
      );


      toc.appendChild(
        button
      );


      tocItems.push(
        button
      );

    }
  );


  // ========================================================
  // Indicator
  // ========================================================

  const indicator =
    document.createElement(
      "div"
    );


  indicator.className =
    "page-indicator";


  const firstNumber =
    document.createElement(
      "span"
    );


  firstNumber.className =
    "page-number";


  firstNumber.textContent =
    "01";


  const lastNumber =
    document.createElement(
      "span"
    );


  lastNumber.className =
    "page-number";


  lastNumber.textContent =
    String(
      pages.length
    ).padStart(
      2,
      "0"
    );


  const seekTrack =
    document.createElement(
      "div"
    );


  seekTrack.className =
    "page-track";


  seekTrack.setAttribute(
    "role",
    "slider"
  );


  seekTrack.setAttribute(
    "tabindex",
    "0"
  );


  seekTrack.setAttribute(
    "aria-label",
    "ページ位置"
  );


  seekTrack.setAttribute(
    "aria-valuemin",
    "1"
  );


  seekTrack.setAttribute(
    "aria-valuemax",
    String(
      pages.length
    )
  );


  const thumb =
    document.createElement(
      "div"
    );


  thumb.className =
    "page-thumb";


  seekTrack.appendChild(
    thumb
  );


  indicator.append(
    firstNumber,
    seekTrack,
    lastNumber
  );


  // ========================================================
  // 長文時だけ使う下部余白
  // ========================================================

  const bottomSpacer =
    document.createElement(
      "div"
    );


  bottomSpacer.className =
    "reader-bottom-spacer";


  // ========================================================
  // DOM
  // ========================================================

  content.append(
    toc,
    wrapper,
    bottomSpacer,
    indicator
  );


  // ========================================================
  // 状態
  // ========================================================

  let activeIndex = 0;

  let previousTocIndex = -1;

  let indicatorHeight = 0;

  let footerHeight = 0;


  // スワイプ

  let pointerId = null;

  let gestureMode = null;

  let startX = 0;

  let startY = 0;

  let currentDragX = 0;


  // Seek

  let seekDragging = false;


  // ========================================================
  // Header
  // ========================================================

  function getHeaderBottom() {

    if (!header) {
      return 0;
    }


    const rect =
      header
        .getBoundingClientRect();


    if (
      rect.bottom <= 0
    ) {
      return 0;
    }


    return Math.max(
      0,
      rect.bottom
    );

  }


  function getReaderTop() {

    return (
      getHeaderBottom()
      +
      8
    );

  }


  // ========================================================
  // 自然な本文高さ
  // ========================================================

  function getNaturalHeight(
    index
  ) {

    const inner =
      pageInners[index];


    if (!inner) {
      return 1;
    }


    return Math.max(
      1,
      Math.ceil(
        inner.scrollHeight
      )
    );

  }


  // ========================================================
  // 固定UI計測
  // ========================================================

  function measureFixedUi() {

    if (
      !isMobile()
    ) {

      indicatorHeight = 0;

      footerHeight = 0;

      return;

    }


    footerHeight =
      footer
        ? footer
            .getBoundingClientRect()
            .height
        : 0;


    indicatorHeight =
      indicator
        .getBoundingClientRect()
        .height;


    document.documentElement
      .style
      .setProperty(
        "--mobile-footer-height",
        `${footerHeight}px`
      );


    document.documentElement
      .style
      .setProperty(
        "--mobile-indicator-height",
        `${indicatorHeight}px`
      );

  }


  // ========================================================
  // 短文ページの最低高さ
  //
  // 現在のwrapper位置から
  // Indicator上端まで
  // ========================================================

  function getReaderFloor() {

    if (
      !isMobile()
    ) {
      return 1;
    }


    const indicatorTop =
      indicator
        .getBoundingClientRect()
        .top;


    const wrapperTop =
      wrapper
        .getBoundingClientRect()
        .top;


    const effectiveTop =
      Math.max(
        wrapperTop,
        getReaderTop()
      );


    return Math.max(
      1,
      Math.floor(
        indicatorTop
        -
        effectiveTop
        -
        1
      )
    );

  }


  // ========================================================
  // track位置
  // ========================================================

  function getPageX(
    index
  ) {

    return (
      -index
      *
      wrapper.clientWidth
    );

  }


  function setTrackX(
    x,
    animate
  ) {

    if (
      animate
      &&
      !reducedMotionQuery.matches
    ) {

      pageTrack.classList.add(
        "is-animating"
      );

    } else {

      pageTrack.classList.remove(
        "is-animating"
      );

    }


    pageTrack.style.transform =
      `translate3d(${x}px, 0, 0)`;

  }


  // ========================================================
  // 深い位置にいたら
  // 高さ変更前にReader上部へ戻す
  // ========================================================

  function alignReaderTopIfNeeded() {

    if (
      !isMobile()
    ) {
      return;
    }


    const desiredTop =
      getReaderTop();


    const actualTop =
      wrapper
        .getBoundingClientRect()
        .top;


    if (
      actualTop <
      desiredTop - 4
    ) {

      window.scrollBy({
        top:
          actualTop
          -
          desiredTop,

        behavior:
          "auto"
      });


      /*
       * 強制reflow
       * Chromeの座標をここで確定させる
       */
      wrapper
        .getBoundingClientRect();

    }

  }


  // ========================================================
  // 現在ページの高さを適用
  // ========================================================

  function applyHeight(
    index
  ) {

    if (
      !isMobile()
    ) {

      wrapper.style.height =
        "";

      bottomSpacer.style.height =
        "";

      return;

    }


    measureFixedUi();


    const naturalHeight =
      getNaturalHeight(
        index
      );


    const floor =
      getReaderFloor();


    document.documentElement
      .style
      .setProperty(
        "--mobile-reader-floor",
        `${floor}px`
      );


    const finalHeight =
      Math.max(
        naturalHeight,
        floor
      );


    wrapper.style.height =
      `${finalHeight}px`;


    /*
     * 長文だけFooter + Indicator分
     * 最後まで上へ持ち上げられる余白
     */

    const longPage =
      naturalHeight >
      floor + 1;


    bottomSpacer.style.height =
      longPage
        ? `${
            footerHeight
            +
            indicatorHeight
            +
            8
          }px`
        : "0px";

  }


  // ========================================================
  // TOC状態
  // ========================================================

  function updateToc(
    index
  ) {

    if (
      index ===
      previousTocIndex
    ) {
      return;
    }


    previousTocIndex =
      index;


    tocItems.forEach(
      (item, itemIndex) => {

        const active =
          itemIndex === index;


        item.classList.toggle(
          "active",
          active
        );


        if (
          active
        ) {

          item.setAttribute(
            "aria-current",
            "page"
          );

        } else {

          item.removeAttribute(
            "aria-current"
          );

        }

      }
    );


    if (
      !isMobile()
    ) {
      return;
    }


    const item =
      tocItems[index];


    if (!item) {
      return;
    }


    const tocRect =
      toc
        .getBoundingClientRect();


    const itemRect =
      item
        .getBoundingClientRect();


    const targetLeft =
      toc.scrollLeft
      +
      itemRect.left
      -
      tocRect.left
      -
      (
        toc.clientWidth
        -
        itemRect.width
      )
      /
      2;


    const max =
      Math.max(
        0,
        toc.scrollWidth
        -
        toc.clientWidth
      );


    toc.scrollTo({
      left:
        clamp(
          targetLeft,
          0,
          max
        ),

      behavior:
        motion()
    });

  }


  // ========================================================
  // Indicator
  // ========================================================

  function updateIndicator(
    index = activeIndex
  ) {

    const ratio =
      pages.length <= 1
        ? 0
        : index
          /
          (
            pages.length - 1
          );


    thumb.style.left =
      `${ratio * 100}%`;


    seekTrack.setAttribute(
      "aria-valuenow",
      String(
        index + 1
      )
    );


    seekTrack.setAttribute(
      "aria-valuetext",

      `${index + 1} / ${pages.length} ${pageTitles[index]}`
    );


    updateToc(
      index
    );

  }


  // ========================================================
  // ページ切替
  // ========================================================

  function activatePage(
    index,
    animate = true
  ) {

    index =
      clamp(
        index,
        0,
        pages.length - 1
      );


    if (
      !isMobile()
    ) {

      const page =
        pages[index];


      const top =
        page
          .getBoundingClientRect()
          .top
        +
        window.scrollY
        -
        getHeaderBottom()
        -
        16;


      window.scrollTo({
        top:
          Math.max(
            0,
            top
          ),

        behavior:
          motion()
      });


      return;
    }


    /*
     * ★重要
     *
     * 旧ページの高さを維持した状態で
     * 先にwindowをReader先頭へ。
     *
     * その後に高さを変える。
     */

    if (
      index !==
      activeIndex
    ) {

      alignReaderTopIfNeeded();

    }


    activeIndex =
      index;


    /*
     * 高さ変更
     */

    applyHeight(
      activeIndex
    );


    /*
     * 横位置変更
     */

    setTrackX(
      getPageX(
        activeIndex
      ),

      animate
    );


    updateIndicator(
      activeIndex
    );

  }


  // ========================================================
  // TOCクリック
  // ========================================================

  tocItems.forEach(
    (item, index) => {

      item.addEventListener(
        "click",

        () => {

          activatePage(
            index,
            true
          );

        },

        {
          signal
        }
      );

    }
  );


  // ========================================================
  // 本文横スワイプ
  //
  // ネイティブ横scrollを使わない
  // ========================================================

  wrapper.addEventListener(
    "pointerdown",

    (event) => {

      if (
        !isMobile()
      ) {
        return;
      }


      if (
        event.pointerType === "mouse"
        &&
        event.button !== 0
      ) {
        return;
      }


      pointerId =
        event.pointerId;


      gestureMode =
        null;


      startX =
        event.clientX;


      startY =
        event.clientY;


      currentDragX =
        getPageX(
          activeIndex
        );


      pageTrack.classList.remove(
        "is-animating"
      );

    },

    {
      signal
    }
  );


  wrapper.addEventListener(
    "pointermove",

    (event) => {

      if (
        !isMobile()
        ||
        pointerId !==
        event.pointerId
      ) {
        return;
      }


      const dx =
        event.clientX
        -
        startX;


      const dy =
        event.clientY
        -
        startY;


      // ----------------------------------------
      // 方向判定
      // ----------------------------------------

      if (
        gestureMode === null
      ) {

        if (
          Math.abs(dx) < 8
          &&
          Math.abs(dy) < 8
        ) {
          return;
        }


        /*
         * 縦操作
         * ↓
         * ブラウザへそのまま渡す
         */

        if (
          Math.abs(dy)
          >
          Math.abs(dx)
        ) {

          gestureMode =
            "vertical";


          return;

        }


        /*
         * 横操作
         */

        gestureMode =
          "horizontal";


        /*
         * 長文の下から横移動する場合、
         * この瞬間に先に上へ避難。
         */

        alignReaderTopIfNeeded();


        try {

          wrapper.setPointerCapture(
            event.pointerId
          );

        } catch (_) {}

      }


      if (
        gestureMode !==
        "horizontal"
      ) {
        return;
      }


      event.preventDefault();


      const minX =
        getPageX(
          pages.length - 1
        );


      const maxX = 0;


      /*
       * 両端で少しだけ抵抗
       */

      let x =
        currentDragX
        +
        dx;


      if (
        x > maxX
      ) {

        x =
          maxX
          +
          (
            x - maxX
          )
          *
          0.25;

      }


      if (
        x < minX
      ) {

        x =
          minX
          +
          (
            x - minX
          )
          *
          0.25;

      }


      setTrackX(
        x,
        false
      );


      /*
       * Indicatorも追従
       */

      if (
        pages.length > 1
      ) {

        const pagePosition =
          clamp(
            -x
            /
            wrapper.clientWidth,

            0,

            pages.length - 1
          );


        const ratio =
          pagePosition
          /
          (
            pages.length - 1
          );


        thumb.style.left =
          `${ratio * 100}%`;

      }

    },

    {
      signal
    }
  );


  function finishSwipe(
    event,
    cancelled = false
  ) {

    if (
      !isMobile()
      ||
      pointerId !==
      event.pointerId
    ) {
      return;
    }


    const dx =
      event.clientX
      -
      startX;


    const threshold =
      Math.max(
        48,
        wrapper.clientWidth
        *
        0.16
      );


    let target =
      activeIndex;


    if (
      !cancelled
      &&
      gestureMode ===
      "horizontal"
    ) {

      if (
        dx <=
        -threshold
      ) {

        target += 1;

      } else if (
        dx >=
        threshold
      ) {

        target -= 1;

      }

    }


    target =
      clamp(
        target,
        0,
        pages.length - 1
      );


    pointerId =
      null;


    gestureMode =
      null;


    activatePage(
      target,
      true
    );

  }


  wrapper.addEventListener(
    "pointerup",

    (event) => {

      finishSwipe(
        event,
        false
      );

    },

    {
      signal
    }
  );


  wrapper.addEventListener(
    "pointercancel",

    (event) => {

      finishSwipe(
        event,
        true
      );

    },

    {
      signal
    }
  );


  // ========================================================
  // Seek操作
  // ========================================================

  function seekRatio(
    clientX
  ) {

    const rect =
      seekTrack
        .getBoundingClientRect();


    if (
      rect.width <= 0
    ) {
      return 0;
    }


    return clamp(
      (
        clientX
        -
        rect.left
      )
      /
      rect.width,

      0,

      1
    );

  }


  function previewSeek(
    clientX
  ) {

    const ratio =
      seekRatio(
        clientX
      );


    thumb.style.left =
      `${ratio * 100}%`;

  }


  seekTrack.addEventListener(
    "pointerdown",

    (event) => {

      if (
        !isMobile()
      ) {
        return;
      }


      seekDragging =
        true;


      seekTrack.classList.add(
        "is-dragging"
      );


      try {

        seekTrack.setPointerCapture(
          event.pointerId
        );

      } catch (_) {}


      previewSeek(
        event.clientX
      );

    },

    {
      signal
    }
  );


  seekTrack.addEventListener(
    "pointermove",

    (event) => {

      if (
        !seekDragging
      ) {
        return;
      }


      previewSeek(
        event.clientX
      );

    },

    {
      signal
    }
  );


  seekTrack.addEventListener(
    "pointerup",

    (event) => {

      if (
        !seekDragging
      ) {
        return;
      }


      seekDragging =
        false;


      seekTrack.classList.remove(
        "is-dragging"
      );


      const ratio =
        seekRatio(
          event.clientX
        );


      const index =
        Math.round(
          ratio
          *
          (
            pages.length - 1
          )
        );


      activatePage(
        index,
        true
      );

    },

    {
      signal
    }
  );


  seekTrack.addEventListener(
    "pointercancel",

    () => {

      seekDragging =
        false;


      seekTrack.classList.remove(
        "is-dragging"
      );


      updateIndicator(
        activeIndex
      );

    },

    {
      signal
    }
  );


  // ========================================================
  // キーボード
  // ========================================================

  seekTrack.addEventListener(
    "keydown",

    (event) => {

      if (
        !isMobile()
      ) {
        return;
      }


      switch (
        event.key
      ) {

        case "ArrowRight":

          event.preventDefault();

          activatePage(
            activeIndex + 1
          );

          break;


        case "ArrowLeft":

          event.preventDefault();

          activatePage(
            activeIndex - 1
          );

          break;


        case "Home":

          event.preventDefault();

          activatePage(0);

          break;


        case "End":

          event.preventDefault();

          activatePage(
            pages.length - 1
          );

          break;

      }

    },

    {
      signal
    }
  );


  // ========================================================
  // PC現在H2
  // ========================================================

  function updateDesktopCurrentPage() {

    if (
      isMobile()
    ) {
      return;
    }


    const referenceY =
      window.scrollY
      +
      getHeaderBottom()
      +
      80;


    let current = 0;


    pages.forEach(
      (page, index) => {

        const top =
          page
            .getBoundingClientRect()
            .top
          +
          window.scrollY;


        if (
          top <=
          referenceY
        ) {

          current =
            index;

        }

      }
    );


    activeIndex =
      current;


    updateToc(
      current
    );

  }


  window.addEventListener(
    "scroll",

    updateDesktopCurrentPage,

    {
      passive: true,
      signal
    }
  );


  // ========================================================
  // resize
  // ========================================================

  function updateLayout() {

    measureFooter();


    if (
      !isMobile()
    ) {

      wrapper.style.height =
        "";


      bottomSpacer.style.height =
        "";


      pageTrack.style.transform =
        "";


      pageTrack.classList.remove(
        "is-animating"
      );


      updateDesktopCurrentPage();


      return;

    }


    /*
     * 横幅変更後、
     * 現在ページ位置を再計算
     */

    setTrackX(
      getPageX(
        activeIndex
      ),

      false
    );


    applyHeight(
      activeIndex
    );


    updateIndicator(
      activeIndex
    );

  }


  window.addEventListener(
    "resize",

    updateLayout,

    {
      signal
    }
  );


  if (
    window.visualViewport
  ) {

    window.visualViewport
      .addEventListener(
        "resize",

        updateLayout,

        {
          passive: true,
          signal
        }
      );

  }


  if (
    mobileQuery.addEventListener
  ) {

    mobileQuery.addEventListener(
      "change",

      updateLayout,

      {
        signal
      }
    );

  }


  // ========================================================
  // 画像等の読み込み後に
  // 現在ページの高さを再計測
  // ========================================================

  if (
    "ResizeObserver" in window
  ) {

    const readerObserver =
      new ResizeObserver(
        () => {

          if (
            isMobile()
          ) {

            applyHeight(
              activeIndex
            );

          }

        }
      );


    pageInners.forEach(
      (inner) => {

        readerObserver.observe(
          inner
        );

      }
    );


    readerObserver.observe(
      indicator
    );


    observers.push(
      readerObserver
    );

  }


  // ========================================================
  // 初期化
  // ========================================================

  updateLayout();


  requestAnimationFrame(
    () => {

      updateLayout();

    }
  );

});
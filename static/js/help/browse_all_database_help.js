function browse_all_database_help() {
    /*
        bootstrap-tour for the "browse all products" views
     */
    var tour = new Tour({
        storage: false,
        backdrop: true,
        steps: [
            {
                title: "Quick Intro",
                placement: "top",
                orphan: true,
                content: "On this page you can view <b>all products</b> from the database."
            },
            {
                element: "#product_table_filter",
                title: "search function (1/2)",
                placement: "top",
                content: "In most cases, you need to perform a search/filter operation first. To search for a keyword in the Product ID or the description field, use this <b>Search</b> field."
            },
            {
                element: "#tour_table_head",
                title: "search function (2/2)",
                placement: "top",
                content: "To perform a more granular, combined search you can use the column specific search field(s). " +
                         "You can also use regular expressions in your search terms. Sorting is possible when clicking on the header text in the columns."
            },
            {
                element: ".buttons-colvis",
                title: "show additional information",
                placement: "top",
                content: "Use this button to show or hide additional information in the table (e.g. the End of Sale Date)."
            },
            {
                element: ".buttons-copy",
                title: "export table information (1/3)",
                placement: "top",
                content: "There are also some export functions available. You can copy the currently visible table content to your clipboard..."
            },
            {
                element: ".buttons-csv",
                title: "export table information (2/3)",
                placement: "top",
                content: "...or download them as CSV file (comma separated values)..."
            },
            {
                element: ".buttons-pdf",
                title: "export table information (3/3)",
                placement: "top",
                content: "...or PDF. Only the visible columns and entries are exported."
            },
            {
                element: "#product_table_length",
                title: "pagination (1/2)",
                placement: "top",
                content: "You can modify the size of a page here..."
            },
            {
                element: ".pagination",
                title: "pagination (2/2)",
                placement: "top",
                content: "...and use this controls to navigate through the pages."
            }
        ],
        onEnd: function (tour) {
            document.body.scrollTop = document.documentElement.scrollTop = 0;
        }
    });

    tour.init();
    tour.start();
}
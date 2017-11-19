module.exports = function (grunt) {

    // Project configuration.
    grunt.initConfig({
        copy: {
            staticfiles: {
                files: [
                    {
                        expand: true,
                        cwd: "node_modules/",
                        src: [
                            'bootstrap/**',
                            'bootstrap-tour/**',
                            'datatables.net/**',
                            'datatables.net-bs/**',
                            'datatables.net-buttons/**',
                            'datatables.net-buttons-bs/**',
                            'datatables.net-fixedheader/**',
                            'datatables.net-fixedheader-bs/**',
                            'datatables.net-plugins/**',
                            'font-awesome/**',
                            'jszip/**',
                            'pdfmake/**',
                            'jquery/**'
                        ],
                        dest: 'static/lib'
                    }
                ]
            }
        },
        clean: {
            dist: [
                'static/lib/*/*',
                'static/lib/*/.*',
                '!static/lib/*/dist',
                '!static/lib/*/js',
                'static/lib/bootstrap/js',
                '!static/lib/*/css',
                '!static/lib/pdfmake/build',
                '!static/lib/font-awesome/css',
                '!static/lib/font-awesome/fonts',
                '!static/lib/bootstrap-tour/build',
                '!static/lib/datatables.net-plugins/**',
                'static/lib/**/*.sh',
                'static/lib/**/*.json',
                'static/lib/**/*.md',
                'static/lib/**/*.txt'
            ]
        }
    });

    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-clean');
};

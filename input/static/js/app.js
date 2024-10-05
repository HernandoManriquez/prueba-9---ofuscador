var app = angular.module('miApp', []);

app.controller('MainController', function($scope, $http) {
    $scope.serverTime = '{{ current_time }}';

    $scope.updateTime = function() {
        $http.get('/get_time').then(function(response) {
            $scope.serverTime = response.data;
        });
    };
});
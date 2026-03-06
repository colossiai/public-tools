dbq_local () {
  local sql="$1"

  local DB_HOST=localhost
  local DB_PORT=3306
  local DB_NAME=testdb
  local DB_USER=root
  local DB_PASS=xxxxxx

  mysqlsh --js \
    --uri="${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
    -e "
    var res = session.runSql(\`${sql}\`);

    var cols = [];
    var c = res.getColumns();
    for (var i = 0; i < c.length; i++) {
        cols.push(c[i].getColumnLabel());
    }

    var out = [];
    var row;

    while ((row = res.fetchOne()) != null) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) {
            obj[cols[i]] = row[i];
        }
        out.push(obj);
    }

    print(JSON.stringify(out, null, 2));
  "
}

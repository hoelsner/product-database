DO
$body$
BEGIN
  IF NOT EXISTS (SELECT * FROM pg_user WHERE usename = 'var_username') THEN
    CREATE ROLE var_username WITH LOGIN PASSWORD 'secret_key';
  END IF;
END
$body$

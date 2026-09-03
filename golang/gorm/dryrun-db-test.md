# gorm不连接真实db，校验SQL

```go

package tmptest

import (
	"testing"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"gorm.io/gorm/schema"
)

func GetDryRunDB() (*gorm.DB, error) {
	db, err := gorm.Open(mysql.New(mysql.Config{
		// go-sql-driver parses the DSN inside gorm.Open, before DryRun can spare
		// us the dial — so it has to be a well-formed DSN even though nothing connects.
		DSN:                       "u:p@tcp(127.0.0.1:3306)/dryrun?parseTime=true",
		SkipInitializeWithVersion: true,
	}), &gorm.Config{
		DryRun:                 true,
		SkipDefaultTransaction: true,
		DisableAutomaticPing:   true,
		Logger:                 logger.Discard,
		NamingStrategy: schema.NamingStrategy{
			SingularTable: true,
		},
	})
	return db, err
}

type User struct {
	UserID int    `gorm:"column:user_id"`
	Status string `gorm:"column:status"`
}

func TestUserQuerySQL(t *testing.T) {
	db, err := GetDryRunDB()
	if err != nil {
		t.Fatal(err)
	}

	stmt := db.
		Model(&User{}).
		Where("user_id = ?", 123).
		Where("status = ?", "active").
		Find(&[]User{}).
		Statement

	t.Log("SQL:", stmt.SQL.String())
	t.Log("Vars:", stmt.Vars)
}


```
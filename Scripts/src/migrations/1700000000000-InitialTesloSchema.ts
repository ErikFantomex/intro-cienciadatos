import { MigrationInterface, QueryRunner } from 'typeorm';

export class InitialTesloSchema1700000000000 implements MigrationInterface {
  name = 'InitialTesloSchema1700000000000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');
    await queryRunner.query(`
      CREATE TABLE IF NOT EXISTS "users" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "email" text NOT NULL,
        "password" text NOT NULL,
        "fullName" text NOT NULL,
        "isActive" boolean NOT NULL DEFAULT true,
        "roles" text[] NOT NULL DEFAULT ARRAY['user']::text[],
        CONSTRAINT "UQ_users_email" UNIQUE ("email"),
        CONSTRAINT "PK_users_id" PRIMARY KEY ("id")
      )
    `);
    await queryRunner.query(`
      CREATE TABLE IF NOT EXISTS "products" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "title" text NOT NULL,
        "price" double precision NOT NULL DEFAULT 0,
        "description" text,
        "slug" text NOT NULL,
        "stock" integer NOT NULL DEFAULT 0,
        "sizes" text[] NOT NULL,
        "gender" text NOT NULL,
        "tags" text[] NOT NULL DEFAULT ARRAY[]::text[],
        "userId" uuid,
        CONSTRAINT "UQ_products_title" UNIQUE ("title"),
        CONSTRAINT "UQ_products_slug" UNIQUE ("slug"),
        CONSTRAINT "PK_products_id" PRIMARY KEY ("id")
      )
    `);
    await queryRunner.query(`
      CREATE TABLE IF NOT EXISTS "product_images" (
        "id" SERIAL NOT NULL,
        "url" text NOT NULL,
        "productId" uuid,
        CONSTRAINT "PK_product_images_id" PRIMARY KEY ("id")
      )
    `);
    await queryRunner.query(`
      DO $$ BEGIN
        ALTER TABLE "products"
          ADD CONSTRAINT "FK_products_userId_users_id"
          FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE NO ACTION;
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$
    `);
    await queryRunner.query(`
      DO $$ BEGIN
        ALTER TABLE "product_images"
          ADD CONSTRAINT "FK_product_images_productId_products_id"
          FOREIGN KEY ("productId") REFERENCES "products"("id") ON DELETE CASCADE;
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$
    `);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS "product_images"');
    await queryRunner.query('DROP TABLE IF EXISTS "products"');
    await queryRunner.query('DROP TABLE IF EXISTS "users"');
  }
}

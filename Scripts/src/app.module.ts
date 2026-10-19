import { join } from 'path';

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ServeStaticModule } from '@nestjs/serve-static';

import { ProductsModule } from './products/products.module';
import { CommonModule } from './common/common.module';
import { SeedModule } from './seed/seed.module';
import { FilesModule } from './files/files.module';
import { AuthModule } from './auth/auth.module';
import { MessagesWsModule } from './messages-ws/messages-ws.module';
import { CryptoModule } from './crypto/crypto.module';
import { HealthController } from './health.controller';

@Module({
  controllers: [HealthController],
  imports: [
    ConfigModule.forRoot(),

    TypeOrmModule.forRoot({
      // ssl: process.env.STAGE === 'prod',
      // extra: {
      //   ssl: process.env.STAGE === 'prod'
      //         ? { rejectUnauthorized: false }
      //         : null,
      // },
      type: 'postgres',
      host: process.env.DB_HOST,
      port: +process.env.DB_PORT,
      database: process.env.DB_NAME,
      username: process.env.DB_USERNAME,
      password: process.env.DB_PASSWORD,      
      autoLoadEntities: true,
      migrations: [join(__dirname, 'migrations/*{.ts,.js}')],
      migrationsRun: true,
      synchronize:
        process.env.NODE_ENV !== 'production' &&
        process.env.ENABLE_DB_SYNCHRONIZE === 'true',
    }),

    ServeStaticModule.forRoot({
      rootPath: join(__dirname,'..','public'), 
    }),

    ProductsModule,

    CommonModule,

    FilesModule,

    AuthModule,

    MessagesWsModule,

    CryptoModule,

    ...(process.env.ENABLE_SEED_ENDPOINT === 'true' &&
    process.env.NODE_ENV !== 'production'
      ? [SeedModule]
      : []),
  ],
})
export class AppModule {}

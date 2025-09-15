import { execFile, ExecFileException } from 'node:child_process';
import * as path from 'node:path';

// Определяем путь к директории со скриптом, находящейся на два уровня выше и в 'ya-cloud'
const scriptDir: string = path.join(__dirname, '..', '..', 'ya-cloud');
const scriptPath: string = path.join(scriptDir, 'create-docker.sh');

console.log(`Запускаем скрипт: ${scriptPath}`);

// Имя ВМ, которое мы хотим передать в скрипт
const vmName = 'gayrat-docker-python1';

const callback = (error: ExecFileException | null, stdout: string, stderr: string): void => {
    // 1. Проверяем ошибку выполнения самого процесса
    if (error) {
        console.error(`Ошибка выполнения скрипта: ${error.message}`);
        // stderr здесь часто содержит более детальную информацию об ошибке
        if (stderr) {
            console.error('Stderr:', stderr);
        }
        // Завершаем выполнение с кодом ошибки
        process.exit(1);
    }

    // 2. Анализируем stderr на наличие ключевого слова "ERROR"
    // Команда yc выводит ошибки в stderr
    if (stderr && stderr.toUpperCase().includes('ERROR:')) {
        console.error('Обнаружена ошибка в выводе yc:');
        console.error(stderr);
        process.exit(1);
    }

    // Если в stderr есть что-то, но это не ошибка (например, предупреждение), выведем это.
    if (stderr) {
        console.warn('Сообщения в stderr (не являются критической ошибкой):', stderr);
    }

    // 3. Если ошибок нет, выводим результат
    console.log('Скрипт успешно выполнен.');

    // Пытаемся распарсить stdout как JSON
    try {
        const result = JSON.parse(stdout);
        if (result && result.id) {
            console.log(`Создана ВМ с ID: ${result.id}`);
        } else {
            console.warn('Вывод не содержит `id` или имеет неожиданную структуру.');
            console.log('Полный вывод stdout:', stdout);
        }
    } catch (parseError) {
        console.warn('Не удалось распарсить stdout как JSON. Возможно, формат вывода не JSON.');
        console.log('Полный вывод stdout:', stdout);
    }
};

execFile(scriptPath, [vmName], {
    // Указываем рабочую директорию, где находится скрипт.
    // Это хорошая практика, если скрипт зависит от относительных путей.
    cwd: scriptDir
}, callback);
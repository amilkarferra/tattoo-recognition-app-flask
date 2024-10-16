document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('imageInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const result = document.getElementById('result');
    const matchedTattoo = document.getElementById('matchedTattoo');
    const uploadedImage = document.getElementById('uploadedImage');
    const matchedImage = document.getElementById('matchedImage');
    const labelList = document.getElementById('labelList');
    const tattooList = document.getElementById('tattooList');
    const databaseTab = document.getElementById('database-tab');
    const addTattooForm = document.getElementById('addTattooForm');
    const addTattooResult = document.getElementById('addTattooResult');
    const maxLabels = document.getElementById('maxLabels');

    analyzeBtn.addEventListener('click', function() {
        if (!imageInput.files || imageInput.files.length === 0) {
            alert('Please select an image first.');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        formData.append('max_labels', maxLabels.value);

        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            uploadedImage.src = data.uploaded_image;
            labelList.innerHTML = '<li class="list-group-item d-flex justify-content-between align-items-center"><strong>Detected Label</strong><strong>Matched Tattoo Label</strong></li>';
            data.labels.forEach((label, index) => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    <span>${label}</span>
                    <span>${data.matched_labels[index] || '-'}</span>
                `;
                labelList.appendChild(li);
            });

            if (data.error) {
                matchedTattoo.innerHTML = `<p class="text-danger">${data.error}</p>`;
                matchedImage.style.display = 'none';
            } else {
                matchedTattoo.innerHTML = `
                    <p><strong>Matched Tattoo:</strong> ${data.match.nombreImagen}</p>
                    <p><strong>Descriptions:</strong> ${data.match.descripciones.map(desc => `${desc.label} (${desc.weight})`).join(', ')}</p>
                `;
                matchedImage.src = `/static/images/${data.match.nombreImagen}`;
                matchedImage.style.display = 'block';
            }
            result.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            matchedTattoo.innerHTML = '<p class="text-danger">An error occurred while analyzing the image.</p>';
        });
    });

    databaseTab.addEventListener('click', loadTattooDatabase);

    function loadTattooDatabase() {
        tattooList.innerHTML = '';

        fetch('/tattoo_database')
            .then(response => response.json())
            .then(data => {
                data.forEach(tattoo => {
                    const tattooItem = document.createElement('div');
                    tattooItem.className = 'tattoo-item d-flex align-items-center mb-3';
                    tattooItem.innerHTML = `
                        <img src="/static/images/${tattoo.nombreImagen}" alt="${tattoo.nombreImagen}" class="me-3" style="max-width: 100px; height: auto;">
                        <div class="flex-grow-1">
                            <h4>${tattoo.nombreImagen}</h4>
                            <p><strong>Descriptions:</strong></p>
                            <ul class="descriptions-list">
                                ${tattoo.descripciones.map(desc => `<li>${desc.label} (Weight: ${desc.weight})</li>`).join('')}
                            </ul>
                            ${tattoo.user_uploaded ? '<p><em>User Uploaded</em></p>' : ''}
                        </div>
                        <div class="d-flex flex-column">
                            <button class="btn btn-sm btn-outline-primary mb-2 edit-btn" data-image="${tattoo.nombreImagen}">Edit</button>
                            <button class="btn btn-sm btn-outline-danger mb-2 delete-btn" data-image="${tattoo.nombreImagen}">Delete</button>
                            <button class="btn btn-sm btn-outline-info recreate-btn" data-image="${tattoo.nombreImagen}">Recreate Description</button>
                        </div>
                    `;
                    tattooList.appendChild(tattooItem);
                });

                document.querySelectorAll('.edit-btn').forEach(btn => {
                    btn.addEventListener('click', editTattoo);
                });
                document.querySelectorAll('.delete-btn').forEach(btn => {
                    btn.addEventListener('click', deleteTattoo);
                });
                document.querySelectorAll('.recreate-btn').forEach(btn => {
                    btn.addEventListener('click', recreateDescription);
                });
            })
            .catch(error => {
                console.error('Error loading tattoo database:', error);
                tattooList.innerHTML = '<p class="text-danger">Error loading tattoo database.</p>';
            });
    }

    function editTattoo(event) {
        const imageName = event.target.dataset.image;
        const tattooItem = event.target.closest('.tattoo-item');
        const descriptionsList = tattooItem.querySelector('.descriptions-list');
        const currentDescriptions = Array.from(descriptionsList.querySelectorAll('li')).map(li => {
            const [label, weight] = li.textContent.split(' (Weight: ');
            return { label, weight: parseFloat(weight) };
        });

        const form = document.createElement('form');
        form.className = 'edit-form mb-2';
        form.innerHTML = `
            <h5>Edit Descriptions and Weights</h5>
            ${currentDescriptions.map((desc, index) => `
                <div class="mb-2">
                    <input type="text" class="form-control mb-1" value="${desc.label}" data-index="${index}">
                    <input type="number" class="form-control" value="${desc.weight}" min="0" max="1" step="0.1" data-index="${index}">
                </div>
            `).join('')}
            <button type="submit" class="btn btn-sm btn-success me-2">Save</button>
            <button type="button" class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
        `;

        descriptionsList.replaceWith(form);
        event.target.style.display = 'none';

        form.querySelector('.cancel-btn').addEventListener('click', () => {
            form.replaceWith(descriptionsList);
            event.target.style.display = 'block';
        });

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const newDescriptions = Array.from(form.querySelectorAll('input[type="text"]')).map((input, index) => ({
                label: input.value,
                weight: parseFloat(form.querySelector(`input[type="number"][data-index="${index}"]`).value)
            }));

            fetch(`/edit_labels/${imageName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ labels: newDescriptions.map(desc => desc.label) }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    return fetch(`/edit_weights/${imageName}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ weights: Object.fromEntries(newDescriptions.map(desc => [desc.label, desc.weight])) }),
                    });
                } else {
                    throw new Error('Failed to update labels');
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    descriptionsList.innerHTML = newDescriptions.map(desc => `<li>${desc.label} (Weight: ${desc.weight})</li>`).join('');
                    form.replaceWith(descriptionsList);
                    event.target.style.display = 'block';
                } else {
                    throw new Error('Failed to update weights');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the tattoo information');
            });
        });
    }

    function deleteTattoo(event) {
        const imageName = event.target.dataset.image;
        if (confirm(`Are you sure you want to delete the tattoo "${imageName}"?`)) {
            fetch(`/delete_tattoo/${imageName}`, {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTattooDatabase();
                } else {
                    alert('Failed to delete tattoo');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting the tattoo');
            });
        }
    }

    function recreateDescription(event) {
        const imageName = event.target.dataset.image;
        const formData = new FormData();
        formData.append('max_labels', document.getElementById('addMaxLabels').value);

        fetch(`/recreate_description/${imageName}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Description recreated successfully');
                loadTattooDatabase();
            } else {
                alert('Failed to recreate description');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while recreating the description');
        });
    }

    addTattooForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(addTattooForm);

        fetch('/add_tattoo', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addTattooResult.innerHTML = `<p class="text-success">${data.message}</p>`;
                addTattooForm.reset();
                loadTattooDatabase();
            } else {
                addTattooResult.innerHTML = `<p class="text-danger">${data.error}</p>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addTattooResult.innerHTML = '<p class="text-danger">An error occurred while adding the tattoo.</p>';
        });
    });
});
